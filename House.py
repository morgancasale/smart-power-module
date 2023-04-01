import numpy as np
import pandas as pd
import datetime
import Server
import matplotlib.pyplot as plt
from dataFromDb import DBRequest
import APIs
from Module import Module
from datetime import datetime, timedelta
class House():
        def __init__(self,houseID,listModules):
          self.houseID=houseID
          self.listModules=listModules
      
        def getlistModules(self):
             return print(self.listModules)
        
        #questo resituisce la somma delle medie delle potenze dei vari moduli in una determinata data e ora
        def getTotalAvgHourly_Power(self,date,hour):
             somma=0
             allModules=self.listModules
             lenghtList=len(self.listModules)-1
             for x in range (lenghtList):
                  powerModuleSelected=allModules[x].getHourlyPowerByDateAndHour(date,hour)
                  somma+=powerModuleSelected
             return somma



        #trova fascia oraria nel giorno (richiesto) in cui la media di potenza è maggiore.
        def getMaxDaily_of_TotalAvgHourly_Power(self,date):
            lenghtFor=23
            maxPower=0
            for x in range (lenghtFor):
                  powerModuleSelected=self.getTotalAvgHourly_Power(date,x)
                  if maxPower<powerModuleSelected:
                       maxPower=powerModuleSelected
                       date_of_max=date
                       hour_of_max=x
                       
            return [maxPower,date_of_max,hour_of_max]



        #questo calcola il consumo giornaliero totale di tutti i moduli
        def getTotalDaily_Power(self,date):
             somma=0
             allModules=self.listModules
             lenghtList=len(self.listModules)-1
             for x in range (lenghtList):
                  powerModuleSelected=allModules[x].getDailyPowerConsumption(date)
                  somma+=powerModuleSelected
             return somma



        #questo calcola il consumo giornaliero medio  di tutti i moduli in un range di date
        def getTotalAvgDaily_Power(self,date1, date2):
             somma=0
             allModules=self.listModules
             lenghtList=len(self.listModules)-1
             for x in range (lenghtList):
                  powerModuleSelected=allModules[x].getDailyAvgPowerConsumptionPeriod(date1,date2)
                  somma+=powerModuleSelected
             return somma


        #questo calcola il consumo settimanale totale  di tutti i moduli in un range di date
        def getTotalWeekly_Power(self,start_data):
             somma=0
             allModules=self.listModules
             lenghtList=len(self.listModules)-1
             for x in range (lenghtList):
                  powerModuleSelected=allModules[x].WeeklyTotalPowerConsumption(start_data)
                  somma+=powerModuleSelected
             return somma


        #questo calcola il consumo settimanale medio  di tutti i moduli in un range di date
        def getAvgWeekly_Power(self,start_data):
             somma=0
             allModules=self.listModules
             lenghtList=len(self.listModules)-1
             for x in range (lenghtList):
                  powerModuleSelected=allModules[x].getWeeklyAvgPowerConsumption(start_data)
                  somma+=powerModuleSelected
             return somma

        #questo trova il giorno nella settimana con consumo totale giornaliero maggiore (restituisce due valori: valorePotenza, datagiorno)
        def getHigherPowerDayinWeek(self,start_data):
          date = datetime.fromisoformat(start_data)
          maxPowerValue=0
          for x in range (7):
               modified_date = date + timedelta(days=x+1)
               textnewdata=datetime.strftime(modified_date,"%Y-%m-%d")
               power_in_day=self.getTotalDaily_Power(textnewdata)
               if maxPowerValue<power_in_day:
                       maxPowerValue=power_in_day
                       date_of_max=textnewdata
                       
          return [maxPowerValue,date_of_max]
        

        #questo calcola consumo potenza totale mensile di tutta casa dato mese e anno
        def getTotalMonthly_Power(self,anno,mese):
             somma=0
             allModules=self.listModules
             lenghtList=len(self.listModules)-1
             for x in range (lenghtList):
                  powerModuleSelected=allModules[x].getMonthlyTotalPowerConsumption(anno,mese)
                  somma+=powerModuleSelected
             return somma



