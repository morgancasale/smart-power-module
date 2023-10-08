import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
import sqlite3
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
    
    def MQTTInterface(self, deviceID, case):
        topic = "/smartSocket/data"
        if case =='ON':
            msg= {
                "deviceID" : deviceID, 
                "states" : [1,1,1]
                }
        else:   
            msg= {
                "deviceID" : deviceID, 
                "states" : [0,0,0]
                }        
        str_msg = json.dumps(msg, indent=2)
        self.client.MQTT.Publish(topic, str_msg)

    
    def update_remove_info(self,repeat,deviceID):
        repeat-=1
        if repeat>0:
            query="UPDATE DeviceScheduling SET repeat = ? WHERE deviceID = ?"
            self.curs.execute(query,(repeat,deviceID))
            self.conn.commit()
        elif repeat==0:
            query="DELETE FROM DeviceScheduling WHERE deviceID = ?"
            self.curs.execute(query, (deviceID,))
            self.conn.commit()
            

    def manageService(self, houseID):
        current_time = time.time()
        deviceSchedule = self.getTimeInfo(houseID)

        for index, row in deviceSchedule.iterrows():
            start_time = row['startTime']
            end_time = row['endTime'] if row['enableEnd'] else None
            deviceID = row['deviceID']
            mode = row['mode']
            repeat=row['repeat']
            time_diff = current_time - start_time
            days_passed = time_diff / (24 * 60 * 60)  
            
            if days_passed >= 1:
                days_to_add = int(days_passed)
                start_time += days_to_add * (24 * 60 * 60)  
                if end_time is not None:
                    end_time += days_to_add * (24 * 60 * 60)  
        
            if current_time == start_time:
                if mode == 'ON':
                    self.MQTTInterface(deviceID,'ON')
                    if end_time is None:
                        self.update_remove_info(repeat,deviceID)
                else:
                    self.MQTTInterface(deviceID,'OFF')
                    if end_time is None:
                        self.update_remove_info(repeat,deviceID)

            if end_time is not None and current_time == end_time:
                if mode == 'ON':
                    self.MQTTInterface(deviceID,'OFF')
                    self.update_remove_info(repeat,deviceID)
                else:
                    self.MQTTInterface(deviceID,'ON')
                    self.update_remove_info(repeat,deviceID)
                    
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
        time.sleep(60)


