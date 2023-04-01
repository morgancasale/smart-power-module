import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataFromDb import DBRequest
from datetime import timedelta, date


class Module():
      def __init__(self,moduleID,df):
          self.moduleID=moduleID
          self.df=df
      
      def showAllData(self):
          print(f"Module: {self.moduleID}, data: {self.df}") 

      #__________________Hourly_____________________

      #resistuisce il dataframe con tutte le potenze per fascia oraria
      def getHourlyAvgData(self):
            df=self.df
            df['day'] = df['date'].dt.date
            df['hour'] = df['date'].dt.hour
            df['minute'] = df['date'].dt.minute          
            HourlyAverageDF=df.groupby(["day","hour"]).agg("mean").reset_index()
            HourlyAverageDF=pd.DataFrame(HourlyAverageDF, columns=['day', 'hour', 'power'])
            return HourlyAverageDF
      #restituisce tutte le fascie orarie con media maggiore nei vari giorni
      def getHourlyAvgDatamax(self):
            HourlyAverageDF=self.getHourlyAvgData()
            maxslot = HourlyAverageDF.groupby(["day"])['power'].max()
            result = pd.merge(HourlyAverageDF, maxslot, on=['power','day'])
            result['hour'] = result['hour'].apply(lambda x: f"{x}-{x+1}")
            result.rename(columns={'hour': 'timeslot'}, inplace=True)
            return result[result['power']!=0]
      
      #questa funzione mi restituisce il valore di potenza media oraria di un specifico giorno e specifica ora
      def getHourlyPowerByDateAndHour(self,date,hour):
           HourlyAverageDF=self.getHourlyAvgData()
          # return HourlyAverageDF.loc[(HourlyAverageDF['day'] == pd.to_datetime(date)) & (HourlyAverageDF['hour'] == hour), 'power'].iloc[0]
           result=HourlyAverageDF.loc[(HourlyAverageDF['day'] == pd.to_datetime(date)) & (HourlyAverageDF['hour'] == hour), 'power']
           if result.empty:
                return 0
           else:
                return result.iloc[0]
           
    #_____________________________________Daily______________________________
      #Questa funzione calcola il consumo giornaliero totale dato un giorno
      def getDailyPowerConsumption(self,date):
            df=self.df
            df['day'] = df['date'].dt.date  # estrai giorno
            dailyPower_cons = df.groupby('day')['power'].sum().reset_index()
            result=dailyPower_cons.loc[(dailyPower_cons['day'] == pd.to_datetime(date)), 'power']
            if result.empty:
                return 0
            else:
                return result.iloc[0]
      #Questa funzione calcola il consumo giornaliero medio tra due date 
      def getDailyAvgPowerConsumptionPeriod(self,date1,date2): 
          df=self.df
          df['date'] = df['date'].dt.date  # estrai giorno    
          df2 = df.loc[df['date'].between( pd.to_datetime(date1),  pd.to_datetime(date2))]
          dailyPower_cons=df2.groupby("date")['power'].sum().reset_index()
          result=dailyPower_cons["power"].mean()
          return result
#_____________________________Weekly______________
       #Questa funzione calcola il consumo  totale settimanale partendo da una data di input e aggiungendo 7 giorni 
      def getWeeklyTotalPowerConsumption(self,start_data):
          end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
          df=self.df
          df['date'] = df['date'].dt.date  # estrai giorno    
          df2 = df.loc[df['date'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
          dailyPower_cons=df2.groupby("date")['power'].sum().reset_index()
          result=dailyPower_cons["power"].sum()
          return result
      
       #Questa funzione calcola il consumo  medio settimanale partendo da una data di input e aggiungendo 7 giorni 
      def getWeeklyAvgPowerConsumption(self,start_data):
          end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
          df=self.df
          df['date'] = df['date'].dt.date  # estrai giorno    
          df2 = df.loc[df['date'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
          dailyPower_cons=df2.groupby("date")['power'].sum().reset_index()
          result=dailyPower_cons["power"].mean()
          return result
        #Questa trova il giorno nella settimana richiesta dove c'è consumo più alto (restituisce un dataframe contenente potenza e data richiesta)
      def getDayinWeekHigherConsumption(self,start_data):
          end_date=pd.to_datetime(start_data)+pd.Timedelta(days=7)
          df=self.df
          df['date'] = df['date'].dt.date  # estrai giorno    
          df2 = df.loc[df['date'].between( pd.to_datetime(start_data),  pd.to_datetime(end_date))]
          week_cons=df2.groupby("date")['power'].sum().reset_index()
          result=week_cons.loc[week_cons['power'].idxmax()]
          if result.empty:
                return 0
          else:
                return result


#____________________________Monthly____________________________
 #Questa funzione calcola il consumo  totale mensile (specificando anno e mese(a numero da 1 a 12))
      def getMonthlyTotalPowerConsumption(self,anno,mese):
          primadata=str(anno)+"-"+str(mese)+"-01"
          ultimadata=str(anno)+"-"+str(mese+1)+"-01"
          df=self.df
          df['date'] = df['date'].dt.date # estrai giorno   
          df2 = df.loc[df['date'].between( pd.to_datetime(primadata),  pd.to_datetime(ultimadata),inclusive='left')]
          monthlyTot=df2.groupby("date")['power'].sum().reset_index()
          result=monthlyTot["power"].sum()
          return result



          
      
      def HourlyAvgData(self):
        HourlyAverage_data=self.df.groupby("date").agg("mean").reset_index()
        HourlyAverage_data['day'] = HourlyAverage_data['date'].dt.date
        HourlyAverage_data['hour'] = HourlyAverage_data['date'].dt.hour
        HourlyAverageDF=pd.DataFrame(HourlyAverage_data, columns=['day', 'hour', 'power'])
        print(f"Hourly Average Data:{HourlyAverageDF}") 
        
        maxslot = HourlyAverageDF.groupby(["day"])['power'].max()
        #print(f"Fasce orarie con consumo maggiore per giorno:{maxslot}")
        result = pd.merge(HourlyAverageDF, maxslot, on=['power','day'])
        print(result)
        for i in range(result.shape[0]):
            print(f"{result['day'][i]} : il maggior consumo di potenza è registrato tra le {result['hour'][i]} e le {result['hour'][i]+1}")
        


      def DailyPowerConsumption(self):
          df['date'] = df['date'].dt.date  # estrai giorno
          dailyPower_cons = df.groupby('date')['power'].sum()
          print(f"Daily Power Consumption:{dailyPower_cons}")

          #Grafico consumo di potenza giornaliero
          date_vector = dailyPower_cons.index
          power_vector=dailyPower_cons.values
          plt.plot(date_vector, power_vector)
          plt.xlabel('Date')
          plt.ylabel('Power')
          plt.show()


      def DailyAvgData(self): 
          df['date'] = df['date'].dt.date  # estrai giorno    
          dailyAverage_data=df.groupby("date").agg("mean")
          print(f"Daily Average Data:{dailyAverage_data}")

          date_vector = dailyAverage_data.index  # vettore di date
          power_vector = dailyAverage_data['power']  # vettore di potenze
          current_vector = dailyAverage_data['current']  # vettore di correnti

          fig,(ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))  # crea 2 subplot verticali
          # primo subplot per la potenza
          ax1.plot(date_vector, power_vector)
          ax1.set_title('Power vs Date')
          ax1.set_xlabel('Date')
          ax1.set_ylabel('Power(W)')
          # secondo subplot per la corrente
          ax2.plot(date_vector, current_vector)
          ax2.set_title('Current vs Date')
          ax2.set_xlabel('Date')
          ax2.set_ylabel('Current (A)')

          plt.tight_layout()  # aggiusta la disposizione dei subplot
          plt.show() 


      def WeeklyAvgData(self):
          df['week'] = df['date'].dt.week
          weeklyAverage_data=df.groupby("week").agg("mean")
          print(f"weekly Average Data:{weeklyAverage_data}")

          

           

      def MonthlyAvgData(self):
          df['month'] = df['date'].dt.month
          monthlyAverage_data=df.groupby("month").agg("mean")
          print(f"Monthly Average Data:{monthlyAverage_data}")

          date_vector = monthlyAverage_data.index  # vettore di date
          power_vector = monthlyAverage_data['power']  # vettore di potenze
          current_vector = monthlyAverage_data['current']  # vettore di correnti

          fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))  # crea 2 subplot verticali
          # primo subplot per la potenza
          ax1.plot(date_vector, power_vector)
          ax1.set_title('Power vs date')
          ax1.set_xlabel('date')
          ax1.set_ylabel('Power(W)')
          # secondo subplot per la corrente
          ax2.plot(date_vector, current_vector)
          ax2.set_title('Current vs date')
          ax2.set_xlabel('date')
          ax2.set_ylabel('Current (A)')

          plt.tight_layout()  
          plt.show() 

      def YearlyAvgData(self):
          df['year'] = df['date'].dt.year
          yearlyAverage_data=df.groupby("year").agg("mean")
          print(f"weekly Average Data:{yearlyAverage_data}")

          date_vector = yearlyAverage_data.index  # vettore di date
          power_vector = yearlyAverage_data['power']  # vettore di potenze
          current_vector = yearlyAverage_data['current']  # vettore di correnti

          fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))  # crea 2 subplot verticali
          # primo subplot per la potenza
          ax1.plot(date_vector, power_vector)
          ax1.set_title('Power vs date')
          ax1.set_xlabel('date')
          ax1.set_ylabel('Power(W)')
          # secondo subplot per la corrente
          ax2.plot(date_vector, current_vector)
          ax2.set_title('Current vs date')
          ax2.set_xlabel('date')
          ax2.set_ylabel('Current (A)')

          plt.tight_layout()  
          plt.show() 
        
      
          
if __name__=="__main__":
    moduleID=input("ModuleID: ")
    DBR = DBRequest()
    response = DBR.getData(1,str(moduleID))
    dataDevice=response.json()
    matrix = np.array(dataDevice)

    # Crea un DataFrame a partire dalla matrice
    df = pd.DataFrame(matrix, columns=['date', 'power', 'current', 'voltage'])
    # Converti la colonna 'data' in formato datetime
    df['date'] = pd.to_datetime(df['date'])
    df['power'] = df['power'].astype(float)
    df['current'] = df['current'].astype(float)
    df['voltage'] = df['voltage'].astype(float)

    module1=Module(moduleID,df)
   # module1.showAllData() 
   # module1.DailyPowerConsumption()
  #  module1.DailyAvgData()
    prova=module1.getHourlyAvgData()
    prova2=module1.getHourlyAvgDatamax()
    ciao=1
   # module1.MonthlyAvgData()
  #  module1.HourlyAvgData()
   #1 module1.YearlyAvgData()
  