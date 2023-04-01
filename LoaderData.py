import numpy as np
import pandas as pd
import datetime
import Server
#import matplotlib.pyplot as plt
from dataFromDb import DBRequest
import APIs
from Module import Module
from House import House
class DataLoader():
    numberHouses=1

    def loadHouseData(self,houseID):
        DBR = DBRequest()
        response = DBR.getData(3,str(houseID))
        data=response.json()
        matrix = np.array(data)

        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(matrix, columns=['id','date', 'power', 'current', 'voltage'])
        df['id'] = pd.to_numeric(df['id'])
        df['date'] = pd.to_datetime(df['date'])
        #df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        df['current'] = df['current'].astype(float)
        df['voltage'] = df['voltage'].astype(float)
        
        
        #Creo una lista di moduli presenti in casa
        allmodules=[]
        #Trovo il numero di moduli presenti: cerco il massimo id presente (=ultimo id_modulo->numero moduli)
        last=df[['id']].max()

        #con il for riempo la lista con ogni modulo presente nel database
        for x in range(int(last.id)):
            #seleziona il modulo con id=x e poi lo aggiunge alla lista
            moduleX=Module(x+1,df[df['id']==x+1])
            allmodules.append(moduleX)

        return House(houseID,allmodules)
    
    def loadAllHouseData(self,):
        allhouses=[]
        for x in range(self.numberHouses):
         allhouses.append(self.loadHouseData(x+1))
        return allhouses