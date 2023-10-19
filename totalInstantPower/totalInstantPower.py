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
import requests

from microserviceBase.serviceBase import *

class House_instantvalues():

    def __init__(self): 
        try:
            config_file = "totalInstantPower.json"
            if(not IN_DOCKER):
                config_file = "totalInstantPower/" + config_file
            self.client = ServiceBase(config_file)
            self.client.start()
            
            HADB_loc = "HADB.db"
            HADB_loc="homeAssistant/HADB/"+ HADB_loc
            
            while(True):
                self.HADBConn = sqlite3.connect(HADB_loc)
                self.HADBCur = self.HADBConn.cursor()  
                self.compute_instantHousesdata()
                time.sleep(30)
        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
    
    """Retrieves information about devices registered in the catalog and selects only those "online" """
    def getDevicesInfo(self):
        try:    
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "Devices", "keyName": "deviceID", "keyValue": "*"}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)
            dev_online = [device for device in result if device["Online"]]
            return dev_online
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
    
    """Retrieves the "online" devices associated with a particular house"""
    def getHouseDevList(self,houseID):
        try:
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "HouseDev_conn", "keyName": "houseID", "keyValue": houseID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            dev_online_list = set(device['deviceID'] for device in self.getDevicesInfo())
            house_onlinedev = [device for device in result if device['deviceID'] in dev_online_list]
            house_onlinedev_list = []
            for row in house_onlinedev:
                house_onlinedev_list.append((row["houseID"], row["deviceID"])) 
            return house_onlinedev_list
        
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)

    """For each online device belonging to a specific home, it finds the associated metadata_ids.
    If the considered device is switched on, then it retrieves the metadata_id of the energy measurement 
    for that device."""
    def selectMetaHAIDs(self,houseID,attribute):
        house_devices= self.getHouseDevList(houseID)
        devices_list=[]
        selectedMetaHAIDs=[] 
        for element in house_devices:
            devices_list.append(element[1])        
        for dev_id in devices_list:
            meta_data = self.client.getMetaHAIDs(dev_id)
            metaHAID=meta_data[attribute]
            selectedMetaHAIDs.append(metaHAID)
        return selectedMetaHAIDs
    
    '''Computes instant values for a specific house'''
    def compute_istantdata(self,houseID):
        try:
            selectedMetaHAIDs=self.selectMetaHAIDs(houseID,'energy')
            if selectedMetaHAIDs!=[]:
                query="""SELECT MAX(last_updated_ts)
                    FROM states 
                    WHERE metadata_id IN ({})
                """.format(','.join('?' for _ in selectedMetaHAIDs))
                self.HADBCur.execute(query,selectedMetaHAIDs)
                recent_timestamp = self.HADBCur.fetchone()[0]   
                thirty_seconds_ago = recent_timestamp - 30
                query="""SELECT SUM(state)
                    FROM states 
                    WHERE metadata_id IN ({}) AND last_updated_ts >= ? AND last_updated_ts <= ?
                    """.format(','.join('?' for _ in selectedMetaHAIDs))
                self.HADBCur.execute(query,(selectedMetaHAIDs+[thirty_seconds_ago,recent_timestamp]))
                total_state = self.HADBCur.fetchone()[0]
                self.HADBConn.close()

                stateTopic = 'homeassistant/sensor/smartSocket/house/state'
                stateMsg = '{"energy_Tot": %f}' % (total_state)

                availabTopic = "homeassistant/sensor/smartSocket/house/status"
                availabMsg = "online"

                self.client.MQTT.Publish(availabTopic, availabMsg)
                self.client.MQTT.Publish(stateTopic, stateMsg)
                return total_state
            else:
                return None
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)    

    """Computes instant values for each house"""
    def compute_instantHousesdata(self):
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
                self.compute_istantdata(houseID)
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)    

if __name__ == "__main__":
    HIV =House_instantvalues()











        
