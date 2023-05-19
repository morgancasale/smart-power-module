import sqlite3
import connect_db as cdb
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
from microserviceBase.serviceBase import *

class MaxPowerControl():

    def __init__(self,DBPath1,DBPath2):
        self.conn1 = cdb.Connect(DBPath1).create_connection()
        self.curs1 = self.conn1.cursor()
        self.conn2 = cdb.Connect(DBPath2).create_connection()
        self.curs2 = self.conn2.cursor()        


    def getlastPower(self,houseID): 
        query1="SELECT\
                       CASE WHEN entity_id = 'sensor.power' THEN '1'\
                            ELSE SUBSTR(entity_id, LENGTH('sensor.power_') + 1, LENGTH(entity_id) - LENGTH('sensor.power_'))\
                       END AS deviceID,state,max(strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch'))) as last_updated\
                FROM states1\
                WHERE entity_id LIKE 'sensor.power%'\
                GROUP BY deviceID"
        self.curs1.execute(query1)
        rows1 = self.curs1.fetchall()
        query2="SELECT houseID, deviceID\
                FROM HouseDev_conn\
                WHERE houseID=?"
        self.curs2.execute(query2,(houseID,))
        rows2 = self.curs2.fetchall()
        combined_results = []
        for row1 in rows1:
            deviceID = row1[0]
            power = row1[1]
            timestamp= row1[2]
            for row2 in rows2:
                if row2[1] == deviceID:
                    houseID = row2[0]
                    combined_results.append((houseID, deviceID,power,timestamp))
        return combined_results
    

    def loadLastPowerDataHouse(self,houseID):
        data=self.getlastPower(houseID)      
        # Crea un DataFrame a partire dalla matrice
        df = pd.DataFrame(data, columns=['houseID','deviceID','power', 'last_update'])
        df['last_update'] = pd.to_datetime(df['last_update'])
        df['power'] = df['power'].astype(float)
        df_selected = df[['deviceID', 'power','last_update']]
        return df_selected
     
    def computeTotalPower(self,houseID):
        df=self.loadLastPowerDataHouse(houseID)
        totalpower=df['power'].sum()    
        return totalpower
    
    def getPowerLimitHouse (self,houseID): 
        query="SELECT powerLimit\
              FROM HouseSettings\
              WHERE houseID=?"
        self.curs2.execute(query,(houseID,))
        rows = self.curs2.fetchall()
        return rows[0][0]      
        
    def getLastUpdate(self,houseID):
        query="SELECT Devices.deviceID, max(Devices.lastUpdate) as lastUpdate,Online\
               FROM Devices,HouseDev_conn\
               WHERE Devices.deviceID=HouseDev_conn.deviceID and houseID=? and online='1'"
        self.curs2.execute(query,(houseID,))
        rows = self.curs2.fetchall()
        return rows     
    
    def controlLastUpdateDevice(self,houseID):    
        data=self.getLastUpdate(houseID)
        df = pd.DataFrame(data, columns=['deviceID','lastUpdate','status'])
        devicetoOFF=df['deviceID'].values[0]
        return devicetoOFF        
        
    def controlPower(self,houseID):
        check=0
        if self.computeTotalPower(houseID)>self.getPowerLimitHouse(houseID):
           check=1    
           self.myMQTTfunction(houseID)         
        else:
           check=0


    def myMQTTfunction(self, houseID):
        deviceID=self.controlLastUpdateDevice(houseID)
        client=ServiceBase("serviceConfig_example.json")
        topic="{}/{}".format(houseID,deviceID)
        msg =[{"MaximumPowerControl":{
                "Active": {
               "moduleState":0 
               }
                }}
         ]
        client.MQTT.start()
        client.MQTT.Subscribe(topic)
        client.MQTT.Publish(topic, msg)
        client.MQTT.stop()       
         
    

if __name__ == "__main__":
  MPC= MaxPowerControl("Data_DB/testDB.db","Data_DB/db.sqlite")
  i=0
    while(i<3): 
        MPC.controlPower("H1")
        i+=1
  
  
  #Recupero gli ultimi dati inseriti per ogni modulo di una specifica casa (data max)
  #test=MPC.getlastPower("H1")
  
  #Creo un dataframe a partire dai dati recuperati
  #test1=MPC.loadLastPowerDataHouse("H1")
  
  #Calcolo potenza totale registrata dalla casa (sommo potenze degli ultimi moduli inseriti)
  #test2=MPC.computeTotalPower("H1")
  
  #Recupero l'info sulla potenza massima di una specifica casa 
  #test3=MPC.getPowerLimitHouse("H1")
  
  #Recupero l'info su quale sia l'ultimo modulo aggiornato nella casa
  #test5=MPC.getLastUpdate("H1")
  
  #Salvo l'id dell'ultimo modulo aggiornato nella casa
  #test6=MPC.controlLastUpdateDevice("H1")
  #Se la potenza totale registrata dalla casa > del treshold per quella stessa casa->aggiorno un flag 
  #quando questo si verifica, spengo (tramite MQTT) l'ultimo modulo aggiornato nella casa
  #test7=MPC.controlPower("H1")

  #ciao=1