import numpy as np
import pandas as pd
import datetime
import Server
from dataFromDb import DBRequest
import APIs

class MaxPowerControl():

    def loadLastPowerDataHouse(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(1,str(houseID))
        data=response.json()
        matrix = np.array(data)

        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(matrix, columns=['moduleID','date', 'power'])
        df['moduleID'] = pd.to_numeric(df['moduleID'])
        df['date'] = pd.to_datetime(df['date'])
        #df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        return df
    
    def computeTotalPower(self,houseID):
        df=self.loadLastPowerDataHouse(houseID)
        totalpower=df['power'].sum()    
        return totalpower
        
        
    def loadHousePowerLimit(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(2,str(houseID))
        data=response.json()
        matrix = np.array(data)

        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(matrix, columns=['houseID','power'])
        #df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        treshold=df['power'].values[0]
        return treshold
    
    def controlLastUpdateModule(self,houseID):    
        DBR = DBRequest()
        response = DBR.getData(4,str(houseID))
        data=response.json()
        matrix = np.array(data)

        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(matrix, columns=['moduleID','lastUpdate','status'])
        df['moduleID'] = pd.to_numeric(df['moduleID'])
        #df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        moduletoOFF=df['moduleID'].values[0]
        return moduletoOFF
        
        
    def controlPower(self,houseID):
        check=0
        if self.computeTotalPower(houseID)>self.loadHousePowerLimit(houseID):
           check=1               
        else:
           check=0
        return check       

    def updateModule(self,houseID):
        if self.controlPower(houseID)==1: 
            DBR = DBRequest()
            DBR.updateData(1,str(self.controlLastUpdateModule(houseID)))
        else:
            return print("Non occorre modifica")    
        
        
    
    def loadAllHouseData(self,):
        numberHouses=2
        allhouses=[]
        for x in range(numberHouses):
         allhouses.append(self.loadLastPowerDataHouse(x+1))
        return allhouses
        
      