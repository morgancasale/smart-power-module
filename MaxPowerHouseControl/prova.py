import sqlite3
import connect_db as cdb
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt

class MaxPowerControl():

    def __init__(self):
        self.conn = cdb.Connect("Data_DB/data.db").create_connection()
        self.curs = self.conn.cursor()
    
    def getlastPower(self,houseID): 
        query="SELECT database.deviceID, max(strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch'))) as date,power\
               FROM database,HouseDev_conn\
               WHERE database.deviceID==HouseDev_conn.deviceID and houseID=?\
               GROUP BY database.deviceID"
        self.curs.execute(query,(houseID,))
        rows = self.curs.fetchall()
        return rows
    
    def loadLastPowerDataHouse(self,houseID):
        data=self.getlastPower(houseID)      
        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(data, columns=['deviceID','date', 'power'])
        df['date'] = pd.to_datetime(df['date'])
        df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        return df
     
    def computeTotalPower(self,houseID):
        df=self.loadLastPowerDataHouse(houseID)
        totalpower=df['power'].sum()    
        return totalpower
    
    def getMaxPowerHouse (self,houseID):
        query="SELECT houseID,maxPower\
              FROM Houses\
              WHERE houseID=?"
        self.curs.execute(query,(houseID,))
        rows = self.curs.fetchall()
        return rows   
    
    def loadHousePowerLimit(self,houseID):
        data=self.getMaxPowerHouse(houseID)
        df = pd.DataFrame(data, columns=['houseID','power'])
        #df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        df['power'] = df['power'].astype(float)
        treshold=df['power'].values[0]
        return treshold    
        
    def getLastUpdate(self,houseID):
        query="SELECT Devices.deviceID, max((lastUpdate)) as date,online\
               FROM Devices,HouseDev_conn\
               WHERE Devices.deviceID=HouseDev_conn.deviceID and houseID=? and online='1'"
        self.curs.execute(query,(houseID,))
        rows = self.curs.fetchall()
        return rows       
    
    def controlLastUpdateModule(self,houseID):    
        data=self.getLastUpdate(houseID)
        df = pd.DataFrame(data, columns=['deviceID','lastUpdate','status'])
        #df['deviceID'] = pd.to_numeric(df['deviceID'])
        #df=df.replace('', 0, regex=True) #nel caso in cui ci fossero caselle vuote
        devicetoOFF=df['deviceID'].values[0]
        return devicetoOFF
        
        
    def controlPower(self,houseID):
        check=0
        if self.computeTotalPower(houseID)>self.loadHousePowerLimit(houseID):
           check=1              
        else:
           check=0
        return check   

    def myMQTTfunction(self, houseID):
        mqtt= MyMQTT(self.clientID,self.broker,1883,subNotifier=None)
        topic="deviceID/moduleState"
        deviceID=self.controlLastUpdateModule(houseID)
        msg =[{"MaximumPowerControl:"{
               "Active": {
               "deviceID":str(deviceID)
               "moduleState":0 
              }} 
              }
             ]
        if self.controlPower(houseID)==1: 
           mqtt.Publish(topic,msg)    
        else:
           return print("Non occorre modifica")
    
        
        mqtt.start()
        mqtt.Subscribe(topic)
        mqtt.Publish(topic, msg)
        mqtt.stop()     
       
    

if __name__ == "__main__":
  MPC= MaxPowerControl()
  #Recupero gli ultimi dati inseriti per ogni modulo di una specifica casa (data max)
  test=MPC.getlastPower("H1")
  #Creo un dataframe a partire dai dati recuperati
  test1=MPC.loadLastPowerDataHouse("H1")
  #Calcolo potenza totale registrata dalla casa (sommo potenze degli ultimi moduli inseriti)
  test2=MPC.computeTotalPower("H1")
  #Recupero l'info sulla potenza massima di una specifica casa 
  test3=MPC.getMaxPowerHouse("H1")
  #Salvo il valore di treshold per la specifica casa
  test4=MPC.loadHousePowerLimit("H1")
  #Recupero l'info su quale sia l'ultimo modulo aggiornato nella casa
  test5=MPC.getLastUpdate("H1")
  #Salvo l'id dell'ultimo modulo aggiornato nella casa
  test6=MPC.controlLastUpdateModule("H1")
  #Se la potenza totale registrata dalla casa > del treshold per quella stessa casa->aggiorno un flag 
  #quando questo si verifica, spengo (tramite MQTT) l'ultimo modulo aggiornato nella casa
  test7=MPC.controlPower("H1")
  ciao=1