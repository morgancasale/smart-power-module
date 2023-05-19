import sqlite3
import connect_db as cdb
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import datetime
import time
import os
import time
import sys

#PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
#sys.path.append(PROJECT_ROOT)
#from microserviceBase.serviceBase import *

class TimeShift():

    def __init__(self):
        self.conn = cdb.Connect("Data_DB/db.sqlite").create_connection()
        self.curs = self.conn.cursor()
    
    def getTimeInfo(self,houseID):       
        query="SELECT DeviceScheduling.deviceID,mode,startSchedule, enableEndSchedule, endSchedule,repeat\
               FROM DeviceScheduling,HouseDev_conn\
               WHERE DeviceScheduling.deviceID==HouseDev_conn.deviceID and houseID=?"
        self.curs.execute(query,(houseID,))
        rows = self.curs.fetchall()
        return rows
    
    def loadTimeInfo(self,houseID):
        data=self.getTimeInfo(houseID)      
        deviceSchedule = pd.DataFrame(data, columns=['deviceID','mode', 'startTime','enableEnd','endTime','repeat'])
        return deviceSchedule
    
    def manageService(self,houseID):
        deviceSchedule=self.loadTimeInfo(houseID)
    
        for index, row in deviceSchedule.iterrows():
         client=ServiceBase("serviceConfig_example.json")
         start_time = row['startTime']
         end_time = row['endTime'] if row['enableEnd'] else None
         current_time=time.time()
         
         for r in range(repeat):
             start_time_repeat = start_time + r * 24 * 60 * 60 
             # Attendo fino al tempo di inizio del servizio
             while time.time() < start_time:
                   time.sleep(1)
            
             # Avvio il servizio
             topic=f"/device/{row['deviceID']}"
             devicestate= 1 if row['mode']=="ON" else 0
             payload=[{"Time Shift": {
                       "Active": {
                       "deviceState": devicestate 
                       }
                      }
                    }]        
             client.MQTT.start()
             client.MQTT.Subscribe(topic)
             client.MQTT.Publish(topic, payload)
             client.MQTT.stop()   
             print(f"Device {row['deviceID']} avviato in modalità {row['mode']} alle {start_time}")
             print(topic)
             print(payload)
             # Se il servizio ha una fine programmata, aspetto fino a quel momento
             if row['enableEnd']:
                while time.time() < end_time:
                      time.sleep(1)             
            
                topic=f"/device/{row['deviceID']}"
                devicestate= 0 if row['mode']=="ON" else 1
                payload=[{"Time Shift": {
                          "Active": {
                          "deviceState": devicestate 
                          }
                         }
                       }]          
            
                client.MQTT.start()
                client.MQTT.Subscribe(topic)
                client.MQTT.Publish(topic, payload)
                client.MQTT.stop()   
                
if __name__ == "__main__":
  TS= TimeShift()
 
  #test=TS.getTimeInfo("H1")
  #test1=TS.loadTimeInfo("H1")
  #print(test1)
  #test2=TS.manageService("H1")
  #print(test2)
  #ciao=1
