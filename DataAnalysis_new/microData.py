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
        df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        condition = df['entity'].str.match(r'^sensor\.(current|voltage|power|energy)(_[0-9]+)?$')
        # Filtriamo il DataFrame in base alla condizione
        df = df[condition]
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
        df = self.loadData()
        # Convertire la colonna 'timestamp' in formato datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:00:00')
        # Raggruppare per 'device' e ora e calcolare le medie
        result = df.groupby(['device_id', 'formatted_timestamp']).mean().reset_index()        
        # Creare una lista delle colonne da trasformare in righe
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        # Inizializzare un DataFrame vuoto per i risultati
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        # Iterare sul DataFrame originale
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['formatted_timestamp']
            # Estrai il numero dopo "D" nel "device_id"
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = f'{col}_avghourly'
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df
    
    def HourlyTotalData(self):  
        df = self.loadData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['formatted_timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:00:00')
        result = df.groupby(['device_id', 'formatted_timestamp']).sum().reset_index()
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['formatted_timestamp']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = f'{col}_tothourly'
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df
    
    def saveHourlyData(self):
        DBR = DBRequest()        
        data_avg = self.HourlyAverageData()
        data_tot = self.HourlyTotalData()
        for i in range(len(data_avg)):
            codeJson_avg = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_avg['entity_id'].iloc[i], data_avg['state'].iloc[i], data_avg['timestamp'].iloc[i])
            codeJson_tot = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_tot['entity_id'].iloc[i], data_tot['state'].iloc[i], data_tot['timestamp'].iloc[i])
            response1= DBR.putData(1, codeJson_avg)
            response2= DBR.putData(1, codeJson_tot)

    
    def loadHourlyData(self):
        DBR = DBRequest()
        response = DBR.getData(2,"0")
        hourlydata=response.json()
        matrix = np.array(hourlydata)
        hourly_df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        hourly_df['attribute'] = hourly_df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
        hourly_df['device_id'] = hourly_df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
        hourly_df['device_id'] = hourly_df['device_id'].apply(lambda x: f"D{x}")
        hourly_df['timestamp'] = pd.to_datetime(hourly_df['timestamp'])
        hourly_df['state'] = hourly_df['state'].astype(float)
        new_columns=['device_id','attribute','state','timestamp']
        hourly_df = hourly_df.reindex(columns=new_columns)
        hourly_df=hourly_df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        result_df = hourly_df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
        return result_df
    
    def dailyAvgData(self):  
        df = self.loadHourlyData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['day'] = df['timestamp'].dt.strftime('%Y-%m-%d 00:00:00')
        result = df.groupby(['device_id', 'day']).mean().reset_index()        
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['day']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = col.replace('_tothourly', '_avgdaily')
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df

    def dailytotData(self):  
        df = self.loadHourlyData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['day'] = df['timestamp'].dt.strftime('%Y-%m-%d 00:00:00')
        result = df.groupby(['device_id', 'day']).sum().reset_index()        
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['day']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = col.replace('_tothourly', '_totdaily')
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df    
    
    def saveDailyData(self):
        DBR = DBRequest()        
        data_avg = self.dailyAvgData()
        data_tot = self.dailytotData()
        for i in range(len(data_avg)):
            codeJson_avg = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_avg['entity_id'].iloc[i], data_avg['state'].iloc[i], data_avg['timestamp'].iloc[i])
            codeJson_tot = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_tot['entity_id'].iloc[i], data_tot['state'].iloc[i], data_tot['timestamp'].iloc[i])
            response1= DBR.putData(1, codeJson_avg)
            response2= DBR.putData(1, codeJson_tot)
    
    def loadDailyData(self):
        DBR = DBRequest()
        response = DBR.getData(3,"0")
        dailydata=response.json()
        matrix = np.array(dailydata)
        daily_df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        daily_df['attribute'] = daily_df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
        daily_df['device_id'] = daily_df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
        daily_df['device_id'] = daily_df['device_id'].apply(lambda x: f"D{x}")
        daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'])
        daily_df['state'] = daily_df['state'].astype(float)
        new_columns=['device_id','attribute','state','timestamp']
        daily_df = daily_df.reindex(columns=new_columns)
        daily_df=daily_df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        result_df = daily_df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
        return result_df
    
    def monthlyAvgData(self):  
        df = self.loadDailyData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.strftime('%Y-%m-01 00:00:00')
        result = df.groupby(['device_id', 'month']).mean().reset_index()        
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['month']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = col.replace('_totdaily', '_avgmonthly')
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df

    def monthlytotData(self):  
        df = self.loadDailyData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.strftime('%Y-%m-01 00:00:00')
        result = df.groupby(['device_id', 'month']).sum().reset_index()        
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['month']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = col.replace('_totdaily', '_totmonthly')
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df    
        
    def saveMonthlyData(self):
        DBR = DBRequest()        
        data_avg=self.monthlyAvgData()
        data_tot = self.monthlytotData()
        for i in range(len(data_tot)):
            codeJson_avg = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_avg['entity_id'].iloc[i], data_avg['state'].iloc[i], data_avg['timestamp'].iloc[i])
            codeJson_tot = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_tot['entity_id'].iloc[i], data_tot['state'].iloc[i], data_tot['timestamp'].iloc[i])
            response1= DBR.putData(1, codeJson_avg) 
            response2=  DBR.putData(1, codeJson_tot)  
            
    
    def loadMonthlyData(self):
        DBR = DBRequest()
        response = DBR.getData(4,"0")
        dailydata=response.json()
        matrix = np.array(dailydata)
        daily_df = pd.DataFrame(matrix, columns=['entity','state', 'timestamp'])
        daily_df['attribute'] = daily_df['entity'].apply(lambda x: x[:-2] if x.endswith('_2') else x)
        daily_df['device_id'] = daily_df['entity'].apply(lambda x: x.split('.')[-1].split('_')[-1] if x.endswith('_2') else '1')
        daily_df['device_id'] = daily_df['device_id'].apply(lambda x: f"D{x}")
        daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'])
        daily_df['state'] = daily_df['state'].astype(float)
        new_columns=['device_id','attribute','state','timestamp']
        daily_df = daily_df.reindex(columns=new_columns)
        daily_df=daily_df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        result_df = daily_df.pivot(index=['device_id','timestamp'], columns='attribute', values='state').reset_index()
        return result_df
    
    def yearlyAvgData(self):  
        df = self.loadMonthlyData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['year'] = df['timestamp'].dt.strftime('%Y-01-01 00:00:00')
        result = df.groupby(['device_id', 'year']).mean().reset_index()        
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['year']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = col.replace('_totmonthly', '_avgyearly')
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df

    def yearlytotData(self):  
        df = self.loadMonthlyData()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['year'] = df['timestamp'].dt.strftime('%Y-01-01 00:00:00')
        result = df.groupby(['device_id', 'year']).sum().reset_index()        
        columns_to_melt = [col for col in result.columns if col.startswith('sensor.')]
        result_df = pd.DataFrame(columns=['entity_id', 'state', 'timestamp'])
        for _, row in result.iterrows():
            device_id = row['device_id']
            timestamp = row['year']
            i = int(device_id[1:])
            for col in columns_to_melt:
                entity_id = col.replace('_totmonthly', '_totyearly')
                if i > 1:
                    entity_id += f'_{i}'
                state = row[col]
                result_df = pd.concat([result_df, pd.DataFrame({'entity_id': [entity_id], 'state': [state], 'timestamp': [timestamp]})])
        return result_df    
        
    def saveYearlyData(self):
        DBR = DBRequest()        
        data_avg=self.yearlyAvgData()
        data_tot = self.yearlytotData()
        for i in range(len(data_tot)):
            codeJson_avg = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_avg['entity_id'].iloc[i], data_avg['state'].iloc[i], data_avg['timestamp'].iloc[i])
            codeJson_tot = '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data_tot['entity_id'].iloc[i], data_tot['state'].iloc[i], data_tot['timestamp'].iloc[i])
            response1= DBR.putData(1, codeJson_avg) 
            response2=  DBR.putData(1, codeJson_tot) 




    def savedata(self,data):
        DBR = DBRequest()        
        for i in range(len(data)):
            codeJson= '{ "entity_id": "%s", "state": %f,"timestamp": "%s"}' % (data['entity_id'].iloc[i], data['state'].iloc[i], data['timestamp'].iloc[i])
            response=  DBR.putData(1, codeJson)

    def hourlyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(6,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['entity_id','state', 'timestamp'])
        # Estrai l'attributo 'attribute' dalla colonna 'Entity_id'
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_tothourly')
        # Aggrega i dati per 'timestamp' e 'attribute' e somma 'state'
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        # Rinomina 'attribute' per includere 'hourly_H1'
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_hourly_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        self.savedata(result_df)
        return result_df
    
    def findmaxinaday(self,houseID):
        df=self.hourlyDataHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Estrai la data (giorno) dalla colonna 'timestamp'
        df['day'] = df['timestamp'].dt.date
        # Esegui il raggruppamento per 'day' e 'attribute' e trova il massimo 'state' e il relativo timestamp
        max_state_df = df.groupby(['day', 'entity_id'])[['state']].max().reset_index()
        result_df = df.merge(max_state_df, on=['day', 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
        result_df['entity_id'] = result_df['entity_id'] + '_max'
        result_df = result_df.drop(columns=['day'])
        result_df['state'] = result_df['state'].astype(int)
        self.savedata(result_df)
        return result_df
    
    def dailyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(7,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totdaily')
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_daily_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        self.savedata(result_df)
        return result_df
    
    def findmaxinamonth(self,houseID):
        df=self.dailyDataHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Estrai la data (giorno) dalla colonna 'timestamp'
        df['month'] = df['timestamp'].dt.to_period('M')
        # Esegui il raggruppamento per 'day' e 'attribute' e trova il massimo 'state' e il relativo timestamp
        max_state_df = df.groupby(['month', 'entity_id'])[['state']].max().reset_index()
        result_df = df.merge(max_state_df, on=['month', 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
        result_df['entity_id'] = result_df['entity_id'] + '_max'
        result_df = result_df.drop(columns=['month'])
        result_df['state'] = result_df['state'].astype(int)
        self.savedata(result_df)
        return result_df
    
    def monthlyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(8,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totmonthly')
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_monthly_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        self.savedata(result_df)        
        return result_df
    
    def findmaxinayear(self,houseID):
        df=self.monthlyDataHouse(houseID)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Estrai la data (giorno) dalla colonna 'timestamp'
        df['year'] = df['timestamp'].dt.to_period('Y')
        # Esegui il raggruppamento per 'day' e 'attribute' e trova il massimo 'state' e il relativo timestamp
        max_state_df = df.groupby(['year', 'entity_id'])[['state']].max().reset_index()
        result_df = df.merge(max_state_df, on=['year', 'entity_id', 'state'], how='inner', suffixes=('', '_max'))
        result_df['entity_id'] = result_df['entity_id'] + '_max'
        result_df = result_df.drop(columns=['year'])
        result_df['state'] = result_df['state'].astype(int)
        self.savedata(result_df)        
        return result_df
    
    def yearlyDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(9,str(houseID))
        data=response.json()
        matrix = np.array(data)
        df = pd.DataFrame(matrix, columns=['entity_id','state', 'timestamp'])
        df['attribute'] = df['entity_id'].str.extract(r'sensor\.(\w+)_totyearly')
        result_df = df.groupby(['timestamp', 'attribute'])['state'].sum().reset_index()
        result_df['attribute'] = 'sensor.' + result_df['attribute'] + f'_yearly_{houseID}'
        result_df['state'] = result_df['state'].astype(int)
        result_df = result_df.rename(columns={'attribute': 'entity_id'})
        self.savedata(result_df)        
        return result_df
    
    def houseslist(self):
        DBR=DBRequest()
        response = DBR.getData(10,"0")
        data=response.json()
        return data
    
    def process_housesdata(self):
        houses_list=['H1','H2']
        # Ciclo su ogni houseID in house_list
        for houseID in houses_list:
            hourly_data = self.hourlyDataHouse(houseID)
            maxh_day = self.findmaxinaday(houseID)
            daily_data=self.dailyDataHouse(houseID)
            maxd_month=self.findmaxinamonth(houseID)
            monthly_data=self.monthlyDataHouse(houseID)
            maxm_year=self.findmaxinayear(houseID)
            yearly_data=self.yearlyDataHouse(houseID)

        
    



    

