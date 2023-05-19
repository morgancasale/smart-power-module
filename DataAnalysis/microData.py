import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataFromDb import DBRequest
from datetime import timedelta, date, datetime

          
class DataAnalysis():

    def loadData(self):
        DBR = DBRequest()
        response = DBR.getData(1,"0")
        data=response.json()
        matrix = np.array(data)

        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        df['attribute'] = df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
        df['device_id'] = df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
        df['device_id'] = df['device_id'].apply(lambda x: f"D{x}")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['state'] = df['state'].astype(float)
        new_columns=['device_id','attribute','state','timestamp']
        df = df.reindex(columns=new_columns)
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        pivot_df = df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
        return pivot_df
    
    def HourlyAverageData(self):
        df=self.loadData()
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.date
        HourlyAverageDF=df.groupby(["device_id","day","hour"]).agg("mean").reset_index()
        # conversione delle stringhe in formato datetime 
        HourlyAverageDF['day'] = pd.to_datetime(HourlyAverageDF['day'])
        # creazione della nuova colonna formato data e ora
        HourlyAverageDF['timestamp'] = HourlyAverageDF['day'].dt.strftime('%Y-%m-%d ') + HourlyAverageDF['hour'].astype(str) + ':00:00'
        return HourlyAverageDF   
    
    def createHourlyAverageDatatable(self):
        DBR = DBRequest()        
        response = DBR.postData(1)

    def saveHourlyAverageData(self):
        DBR = DBRequest()        
        data = self.HourlyAverageData()
        for i in range(len(data)):
            codeJson = '{ "deviceID": "%s", "Voltage": %f, "Current": %f, "Power": %f, "timestamp": "%s"}' % (data['device_id'][i], data['sensor.voltage'][i], data['sensor.current'][i], data['sensor.power'][i], data['timestamp'][i])
            response = DBR.putData(1, codeJson)
    
    def getHourlyPowermax(self):
        HourlyAverageDF=self.HourlyAverageData()
        maxslot = HourlyAverageDF.groupby(["device_id","day"])['sensor.power'].max()
        result = pd.merge(HourlyAverageDF, maxslot, on=['sensor.power','day'])
        result['hour'] = result['hour'].apply(lambda x: f"{x}-{x+1}")
        result.rename(columns={'hour': 'timeslot'}, inplace=True)
        return result[result['sensor.power']!=0]
      
    def DailyData(self):
        DBR = DBRequest()
        response = DBR.getData(2,"0")
        data=response.json()
        matrix = np.array(data)

        df = pd.DataFrame(matrix, columns=['deviceID','timestamp', 'power','current','voltage'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df
    
    def createDailyDatatable(self):
        DBR = DBRequest()        
        response = DBR.postData(2)
    
    def saveDailyData(self):
        DBR = DBRequest()        
        data = self.DailyData()
        for i in range(len(data)):
            codeJson = '{ "deviceID": "%s", "Voltage": %f, "Current": %f, "Power": %f, "timestamp": "%s"}' % (data['deviceID'][i], data['voltage'][i], data['current'][i], data['power'][i], data['timestamp'][i])
            response = DBR.putData(2, codeJson)

    def getDailyPowerConsumption(self,timestamp,deviceID):
        dailyCons=self.DailyData()
        dailyCons['day'] = dailyCons['timestamp'].dt.date  # estrai giorno
        result=dailyCons.loc[(dailyCons['day'] == pd.to_datetime(timestamp)) & (dailyCons['deviceID']==deviceID), 'power']
        if result.empty:
            return 0
        else:
            return result.iloc[0]

    def getDailyAvgPowerConsumptionPeriod(self,date1,date2,deviceID): 
        df=self.DailyData()
        df['day'] = df['timestamp'].dt.date
        df2 = df.loc[df['day'].between( pd.to_datetime(date1),  pd.to_datetime(date2))]
        dailyPowerCons=df2.groupby("deviceID")["power"].mean().reset_index()
        result=dailyPowerCons.loc[(dailyPowerCons['deviceID'] == deviceID),'power']
        if result.empty:
            return 0
        else:
            return result.iloc[0]  
    
    def getWeeklyTotalPowerConsumption(self,start_data,deviceID):
        end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
        df=self.DailyData()
        df['day'] = df['timestamp'].dt.date   
        df2 = df.loc[df['day'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
        weeklyCons=df2.groupby("deviceID")['power'].sum().reset_index()
        result=weeklyCons.loc[(weeklyCons['deviceID']==deviceID),'power']
        return result.iloc[0]
    
    def getWeeklyAvgPowerConsumption(self,start_data,deviceID):
        end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
        df=self.DailyData()
        df['day'] = df['timestamp'].dt.date   
        df2 = df.loc[df['day'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
        weeklyCons=df2.groupby("deviceID")['power'].mean().reset_index()
        result=weeklyCons.loc[(weeklyCons['deviceID']==deviceID),'power']
        return result.iloc[0]
           
    def getDayinWeekHigherConsumption(self,start_data,deviceID):
        end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
        df=self.DailyData()
        df['day'] = df['timestamp'].dt.date   
        df2 = df.loc[df['day'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
        weeklyCons=df2.groupby("deviceID").max("power").reset_index()
        result = pd.merge(weeklyCons, df2, on=['power','deviceID'])
        result=result.loc[(result['deviceID']==deviceID), 'day']
        if result.empty:
            return 0
        else:
            return (result.iloc[0]).strftime('%Y-%m-%d')

    def getDayinMonthHigherConsumption(self,year,month,deviceID):
        firstdate=str(year)+"-"+str(month)+"-01"
        lastdate=str(year)+"-"+str(month+1)+"-01"
        df=self.DailyData()
        df['day'] = df['timestamp'].dt.date   
        df2 = df.loc[df['timestamp'].between( pd.to_datetime(firstdate),  pd.to_datetime(lastdate),inclusive='left')]
        monthlyCons=df2.groupby("deviceID").max("power").reset_index()
        result = pd.merge(monthlyCons, df2, on=['power','deviceID'])
        result=result.loc[(result['deviceID']==deviceID), 'day']
        if result.empty:
            return 0
        else:
            return (result.iloc[0]).strftime('%Y-%m-%d')
    
    def MonthlyData(self):
        DBR = DBRequest()
        response = DBR.getData(3,"0")
        data=response.json()
        matrix = np.array(data)

        df = pd.DataFrame(matrix, columns=['deviceID','year_month', 'power','current','voltage'])
        df['year_month'] = pd.to_datetime(df['year_month'])
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df    
    
    def createMonthlyDatatable(self):
        DBR = DBRequest()        
        response = DBR.postData(3)
            
    def saveMonthlyData(self):
        DBR = DBRequest()        
        data = self.MonthlyData()
        for i in range(len(data)):
            codeJson = '{ "deviceID": "%s", "Voltage": %f, "Current": %f, "Power": %f, "timestamp": "%s"}' % (data['deviceID'][i], data['voltage'][i], data['current'][i], data['power'][i], data['year_month'][i])
            response = DBR.putData(3, codeJson)
            
    def getMonthlyPowerConsumption(self,year,month,deviceID):
        date=str(year)+"-"+str(month)+"-01"
        df=self.MonthlyData()
        result=df.loc[(df['year_month'] == pd.to_datetime(date)) & (df['deviceID']==deviceID), 'power']
        if result.empty:
            return 0
        else:
            return result.iloc[0]

    def getMonthinYearHigherConsumption(self,year,deviceID):
        firstyear=str(year)
        lastyear=str(year+1)
        df=self.MonthlyData()  
        df['year'] = df['year_month'].dt.year 
        df['month'] = df['year_month'].dt.month
        df2 = df.loc[df['year_month'].between( pd.to_datetime(firstyear),  pd.to_datetime(lastyear),inclusive='left')]
        monthlyCons = df2.loc[df.groupby('deviceID')['power'].idxmax()]
        result=monthlyCons.loc[(monthlyCons['deviceID']==deviceID), 'month']
        if result.empty:
            return 0
        else:
            return result.iloc[0]      

    def YearlyData(self):
        DBR = DBRequest()
        response = DBR.getData(4,"0")
        data=response.json()
        matrix = np.array(data)

        df = pd.DataFrame(matrix, columns=['deviceID','year', 'power','current','voltage'])
        df['year'] = pd.to_datetime(df['year'])
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df            
    
    def createYearlyDatatable(self):
        DBR = DBRequest()        
        response = DBR.postData(4)
            
    def saveYearlyData(self):
        DBR = DBRequest()        
        data = self.YearlyData()
        for i in range(len(data)):
            codeJson = '{ "deviceID": "%s", "Voltage": %f, "Current": %f, "Power": %f, "timestamp": "%s"}' % (data['deviceID'][i], data['voltage'][i], data['current'][i], data['power'][i], data['year'][i])
            response = DBR.putData(4, codeJson)   

    def getYearlyPowerConsumption(self,year,deviceID):
        date=str(year)
        df=self.YearlyData()
        result=df.loc[(df['year'] == pd.to_datetime(date)) & (df['deviceID']==deviceID), 'power']
        if result.empty:
            return 0
        else:
            return result.iloc[0]         
          
    def HourlyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(5,str(houseID))
        data=response.json()
        matrix = np.array(data)
        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(matrix, columns=['houseID','deviceID','timestamp', 'voltage','current','power'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        new_columns=['deviceID','timestamp','voltage','current','power']
        df = df.reindex(columns=new_columns)
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df.drop_duplicates()
    
    def getHourlyPowermaxHouse(self,houseID):
        hourlyData=self.HourlyDataHouse(houseID)
        hourlyData['hour'] = hourlyData['timestamp'].dt.hour
        hourlyData['day'] = hourlyData['timestamp'].dt.date
        maxslot = hourlyData.groupby(["deviceID","day"])['power'].max()
        result = pd.merge(hourlyData, maxslot, on=['power','day'])
        result['hour'] = result['hour'].apply(lambda x: f"{x}-{x+1}")
        result.rename(columns={'hour': 'timeslot'}, inplace=True)
        return result[result['power']!=0]
    
    def DailyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(6,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['houseID','deviceID','timestamp', 'voltage','current','power'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        new_columns=['deviceID','timestamp','voltage','current','power']
        df = df.reindex(columns=new_columns)
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df.drop_duplicates()    

    def DailyConsumptionsHouse(self,houseID):
        df=self.DailyDataHouse(houseID)
        df['day'] = df['timestamp'].dt.date 
        dailyCons=df.groupby(["day"]).agg("sum").reset_index()
        # conversione delle stringhe in formato datetime 
        dailyCons['day'] = pd.to_datetime(dailyCons['day'])
        return dailyCons
    
    def DailyAvgConsumptionsHouse(self,houseID):
        df=self.DailyDataHouse(houseID)
        df['day'] = df['timestamp'].dt.date 
        dailyavgCons=df.groupby(["day"]).agg("mean").reset_index()
        # conversione delle stringhe in formato datetime 
        dailyavgCons['day'] = pd.to_datetime(dailyavgCons['day'])
        return dailyavgCons        

    def getDailyAvgPowerConsumptionPeriodHouse(self,houseID,date1,date2): 
        df=self.DailyDataHouse(houseID)
        df['day'] = df['timestamp'].dt.date
        df2 = df.loc[df['day'].between( pd.to_datetime(date1),  pd.to_datetime(date2))]
        dailyavgPowerCons=df2.groupby("deviceID")["power"].mean().reset_index()
        return dailyavgPowerCons
    
    def getDailyTotPowerConsumptionPeriodHouse(self,houseID,date1,date2): 
        df=self.DailyDataHouse(houseID)
        df['day'] = df['timestamp'].dt.date
        df2 = df.loc[df['day'].between( pd.to_datetime(date1),  pd.to_datetime(date2))]
        dailytotPowerCons=df2.groupby("deviceID")["power"].sum().reset_index()
        return dailytotPowerCons
    
    def getWeeklyTotalPowerConsumptionHouse(self,start_data,houseID):
        end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
        df=self.DailyDataHouse(houseID)
        df['day'] = df['timestamp'].dt.date   
        df2 = df.loc[df['day'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
        weeklytotCons=df2.groupby("deviceID")['power'].sum().reset_index()
        return weeklytotCons
    
    def getWeeklyAvgPowerConsumptionHouse(self,start_data,houseID):
        end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
        df=self.DailyDataHouse(houseID)
        df['day'] = df['timestamp'].dt.date   
        df2 = df.loc[df['day'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
        weeklytotCons=df2.groupby("deviceID")['power'].mean().reset_index()
        return weeklytotCons   
      
    def MonthlyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(7,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['houseID','deviceID','timestamp', 'voltage','current','power'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        new_columns=['deviceID','timestamp','voltage','current','power']
        df = df.reindex(columns=new_columns)
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df.drop_duplicates()
    
    def MonthlyConsumptionsHouse(self,houseID):
        df=self.MonthlyDataHouse(houseID)
        monthlytotCons=df.groupby(["timestamp"]).agg("sum").reset_index()
        return monthlytotCons
    
    def MonthlyAvgConsumptionsHouse(self,houseID):
        df=self.MonthlyDataHouse(houseID)
        monthlyavgCons=df.groupby(["timestamp"]).agg("mean").reset_index()
        return monthlyavgCons      
    
    def getMonthinYearwithMaxPowerConsHouse(self,houseID,year):
        df=self.MonthlyConsumptionsHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_year = df[df['timestamp'].dt.year == year]
        result = df_year.loc[df_year['power'].idxmax(), 'timestamp'].month
        if pd.isnull(result):
            return 0
        else:
            return result   
    
    def YearlyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(8,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['houseID','deviceID','timestamp', 'voltage','current','power'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        new_columns=['deviceID','timestamp','voltage','current','power']
        df = df.reindex(columns=new_columns)
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        return df.drop_duplicates()
    
    def YearlyConsumptionsHouse(self,houseID):
        df=self.YearlyDataHouse(houseID)
        yearlytotCons=df.groupby(["timestamp"]).agg("sum").reset_index()
        return yearlytotCons
    
    def YearlyAvgConsumptionsHouse(self,houseID):
        df=self.YearlyDataHouse(houseID)
        yearlyavgCons=df.groupby(["timestamp"]).agg("mean").reset_index()
        return yearlyavgCons  
    
    def getYearwithMaxPowerConsHouse(self,houseID):
        df=self.YearlyConsumptionsHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        result = df.loc[df['power'].idxmax(), 'timestamp'].year
        if pd.isnull(result):
            return 0
        else:
            return result   