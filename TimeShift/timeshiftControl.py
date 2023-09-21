import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
import sqlite3
import connect_db as cdb
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt

from microserviceBase.serviceBase import *

class TimeShift():

    def __init__(self):
        self.conn = sqlite3.connect("Data_DB/db.sqlite")
        self.curs = self.conn.cursor()        
        self.client = ServiceBase("codici/serviceConfig_example.json")
        self.client.start()
    
    def getTimeInfo(self,houseID):       
        query="SELECT DeviceScheduling.deviceID,mode,startSchedule, enableEndSchedule, endSchedule,repeat\
                FROM DeviceScheduling,HouseDev_conn\
                WHERE DeviceScheduling.deviceID==HouseDev_conn.deviceID and houseID=?"
        self.curs.execute(query,(houseID,))
        rows = self.curs.fetchall()
        deviceSchedule = pd.DataFrame(rows, columns=['deviceID','mode', 'startTime','enableEnd','endTime','repeat'])
        return deviceSchedule
    
    def manageService(self,houseID):
        deviceSchedule=self.getTimeInfo(houseID)
    
        for index, row in deviceSchedule.iterrows():
            start_time = row['startTime']
            end_time = row['endTime'] if row['enableEnd'] else None
            current_time=time.time()
            repeat=row['repeat']
            deviceID=row['deviceID']
            mode=row['mode']

            for r in range(repeat):
                start_time_repeat = start_time + r * 24 * 60 * 60 
                print('start_time',start_time_repeat)
                # Attendo fino al tempo di inizio del servizio
                while time.time() < start_time:
                    time.sleep(1)
            
                # Avvio il servizio 
                if mode=='ON':
                    topic="/smartSocket/data" 
                    msg= {
                            "deviceID" : deviceID, 
                            "states" : [1,1,1]
                            }
                    str_msg = json.dumps(msg, indent=2)
                    self.client.MQTT.Publish(topic, str_msg)
                    #self.client.MQTT.stop() 
                    
                    # Se il servizio ha una fine programmata, aspetto fino a quel momento
                    if row['enableEnd']:
                        while time.time() < end_time:
                            time.sleep(1)            
            
                        topic="/smartSocket/data" 
                        msg= {
                            "deviceID" : deviceID, 
                            "states" : [0,0,0]
                            }
                        str_msg = json.dumps(msg, indent=2)
                        self.client.MQTT.Publish(topic, str_msg)
                        #self.client.MQTT.stop() 

    def manageServiceforall(self):
        query="SELECT houseID\
                FROM Houses"
        self.curs.execute(query)
        rows= self.curs.fetchall()
        houses_list = [item[0] for item in rows]
        for houseID in houses_list:
            self.manageService(houseID)
            

if __name__ == "__main__":
    TS=TimeShift()
    while(True):
        TS.manageServiceforall()
        time.sleep(1)

