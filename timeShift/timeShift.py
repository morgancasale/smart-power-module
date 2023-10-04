import os
import time
import sys


IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import requests
from calendar import timegm

from microserviceBase.serviceBase import *

class TimeShift():
    def __init__(self):
        try:
            config_file = "timeShift.json"
            if(not IN_DOCKER):
                config_file = "timeShift/" + config_file
            self.client = ServiceBase(config_file)
            self.client.start()

            while(True):
                self.manageServiceforall()
                time.sleep(60)

        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise Exception(message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Exception(message)


    def getCatalogInfo(self, table, keyName, keyValue, verbose=False):
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": table, "keyName": keyName, "keyValue": keyValue, "verbose": verbose}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            return result
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
    def getHouseList(self):
        result = self.getCatalogInfo("Houses", "houseID", "*")

        house_list = [row["houseID"] for row in result]
        if not type(house_list) is list:
            house_list = [house_list]
        return house_list
    
    def getTimeInfo(self,houseID):       
        try:
            schedules = self.getCatalogInfo("DeviceScheduling", "deviceID", "*")
            
            combined_results = []
            #houses_devs_list = self.getHouseDevList()
            for devSchedules in schedules:
                for schedule in devSchedules:
                    scheduleID = schedule["scheduleID"]
                    deviceID = schedule["deviceID"]
                    socketID = schedule["socketID"]
                    mode = schedule["mode"]
                    startTime = schedule["startSchedule"]
                    enableEnd = schedule["enableEndSchedule"]
                    endTime = schedule["endSchedule"]
                    repeat = schedule["repeat"]
                    combined_results.append((houseID, scheduleID, deviceID, socketID, mode,startTime,enableEnd,endTime,repeat))
   
            return combined_results
         
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)    
            

  
    def MQTTInterface(self, deviceID, socketID, case):
        topic = "/smartSocket/control"

        states = [-1,-1,-1]
        states[socketID] = 1 if case == 'ON' else 0  
        msg = {
            "deviceID" : deviceID, 
            "states" : states
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
    
    def update_remove_info(self, repeat, scheduleID):
        repeat -= 1
        if repeat > 0:
            try:
                catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
                catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
                url = "%s:%s/setDeviceSettings" % (catalogAddress, str(catalogPort))
                data = {"scheduleID": scheduleID, "repeat": repeat}
                requests.put(url, json=data)
            except HTTPError as e:
                message = "An error occurred while updating info in catalog " + e._message
                raise HTTPError(status=e.status, message=message)
            except Exception as e:
                message = "An error occurred while updating info in catalog " + str(e)
                raise Server_Error_Handler.InternalServerError(message=message)
                
        elif repeat==0:
            try:
                catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
                catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
                url = "%s:%s/delDevSchedule" % (catalogAddress, str(catalogPort))
                params = {"table": "DeviceScheduling", "keyName": "scheduleID", "keyValue": scheduleID}      
                
                requests.delete(url, params=params)
            except HTTPError as e:
                message = "An error occurred while retriving info from catalog " + e._message
                raise HTTPError(status=e.status, message=message)
            except Exception as e:
                message = "An error occurred while retriving info from catalog " + str(e)
                raise Server_Error_Handler.InternalServerError(message=message)
            

    def manageService(self, houseID):
        current_time = time.time()
        comb_res = self.getTimeInfo(houseID)
        deviceSchedule = pd.DataFrame(comb_res, columns=['houseID', 'scheduleID', 'deviceID', 'socketID', 'mode', 'startTime', 'enableEnd', 'endTime', 'repeat'])

        for index, row in deviceSchedule.iterrows():
            start_time = timegm(time.strptime(row['startTime'], "%d/%m/%Y %H:%M"))

            end_time = row['endTime'] if row['enableEnd'] else None
            deviceID = row['deviceID']
            scheduleID = row['scheduleID']
            socketID = row['socketID']
            mode = row['mode']
            repeat = row['repeat']
            time_diff = current_time - start_time
            days_passed = time_diff / (24 * 60 * 60)  
            
            if days_passed >= 1:
                days_to_add = int(days_passed)
                start_time += days_to_add * (24 * 60 * 60)  
                if end_time is not None:
                    end_time += days_to_add * (24 * 60 * 60)  
        
            if current_time >= start_time:
                self.MQTTInterface(deviceID, socketID, mode)
                if end_time is None:
                    self.update_remove_info(repeat, scheduleID)

            if end_time is not None and current_time >= end_time:
                not_mode = 'OFF' if mode == 'ON' else 'ON'
                self.MQTTInterface(deviceID, socketID, not_mode)
                self.update_remove_info(repeat, scheduleID)
                    
                    
    def manageServiceforall(self):
        try:
            house_list = self.getHouseList()
            for houseID in house_list:
                self.manageService(houseID)
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message) 
            

if __name__ == "__main__":
    TS = TimeShift()


