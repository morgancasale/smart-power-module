import os
import time
import sys


IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

import sqlite3
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import requests

from microserviceBase.serviceBase import *

class TimeShift():
    def __init__(self):
        try:
            config_file = "TimeShift.json"
            if(not IN_DOCKER):
                config_file = "TimeShift/" + config_file
            self.client = ServiceBase(config_file)
            self.client.start()

            testDB_loc = "testDB.db"
            if(not IN_DOCKER):
                testDB_loc = "TimeShift/" + testDB_loc
            self.DBConn = sqlite3.connect(testDB_loc)
            self.DBCurs = self.DBConn.cursor()  

            while(True):
                self.manageServiceforall()
                time.sleep(60)
        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)


    def getHouseDevList(self):
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "HouseDev_conn", "keyName": "houseID", "keyValue": "*"}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            house_dev_list = []
            for row in result:
                house_dev_list.append((row["houseID"], row["deviceID"]))
            return house_dev_list
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
    
    def getTimeInfo(self,houseID):       
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "DeviceScheduling", "keyName": "", "keyValue": "*"}          
            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)
            
            houses_devs_list = self.getHouseDevList()
            for row1 in rows1:
            deviceID = row1[0]
            mode = row1[1]
            startTime= row1[2]
            enableEnd= row1[3]
            endTime= row1[4]
            repeat= row1[5]
            for row2 in houses_devs_list:
                if row2[1] == deviceID:
                    houseID = row2[0]
                    combined_results.append((houseID, deviceID,mode,startTime,enableEnd,endTime,repeat))
   
            return combined_results
         
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)    
            

  
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

    '''
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
            '''
    
     def update_remove_info(self,repeat,deviceID):
        repeat-=1
        if repeat>0:
            try:
                catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
                catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
                url = "%s:%s/setDeviceSettings" % (catalogAddress, str(catalogPort))
                data={"deviceID":deviceID,"repeat":repeat}
                data=json.dumps(data)
                requests.put(url, json=data)            
                
        elif repeat==0:
            try:
                catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
                catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
                url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
                params = {"table": "DeviceScheduling", "keyName": "deviceID", "keyValue": "*"}      
                
                requests.delete(url, params=params) 
            

      def manageService(self, houseID):
        current_time = time.time()
        comb_res = self.getTimeInfo(houseID)
        deviceSchedule = pd.DataFrame(comb_res, columns=['deviceID','mode', 'startTime','enableEnd','endTime','repeat'])

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
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "Houses", "keyName": "houseID", "keyValue": "*"}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            house_list = [row["houseID"] for row in result]
            for houseID in house_list:
                self.manageService(houseID)
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message) 
            

if __name__ == "__main__":
    TS=TimeShift()
    '''
    while(True):
        TS.manageServiceforall()
        time.sleep(60)
        '''


