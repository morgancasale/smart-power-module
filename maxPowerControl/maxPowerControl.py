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

class maxPowerControl():

    def __init__(self):
        try:
            config_file = "maxPowerControl.json"
            if(not IN_DOCKER):
                config_file = "maxPowerControl/" + config_file
            self.client = ServiceBase(config_file)
            self.client.start()

            HADB_loc = "HADB.db"
            HADB_loc = "homeAssistant/HADB/"+ HADB_loc #da aggiornare poi con home assistant

            self.HADBConn = sqlite3.connect(HADB_loc)
            self.HADBCur = self.HADBConn.cursor()  

            while(True):
                self.controlPowerforall()
                time.sleep(5)
        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise Exception(message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Exception(message)
            
    
    """Gets the device_id from the metadata_id """
    def getDeviceID(self, metaHAID):
        try:
            query = "SELECT entity_id FROM states_meta WHERE metadata_id = ?"
            self.HADBCur.execute(query,(metaHAID,))
            rows = self.HADBCur.fetchall()    
            if rows:
                entity_id = rows[0][0]
                parts = entity_id.split(".")
                deviceID = (parts[1].split("_")[-2].title())
                return deviceID
        except HTTPError as e:
                message = "An error occurred while retriving info from catalog " + e._message
                raise HTTPError(status=e.status, message=message)
        except Exception as e:
                message = "An error occurred while retriving info from catalog " + str(e)
                raise Server_Error_Handler.InternalServerError(message=message)    
    

    """ Checks the latest switches states to determine whether the device is ON or OFF.
        If at least one of the 3 switches associated with a 'Dx' device is 'on', then 'Dx' is ON (True).
        Vice versa, it is off (False)."""
    def getswitchesStates(self, HAIDs):
        stateList=[]
        for element in HAIDs:
            query="""SELECT metadata_id, state,MAX(last_updated_ts)
                    FROM states
                    WHERE metadata_id = ?"""
            self.HADBCur.execute(query,(element,))
            rows = self.HADBCur.fetchone()[1]    
            if rows == 'off'.lower():
                switchState= 0
            else : switchState=1
            stateList.append(switchState)
        deviceState= sum(stateList)
        if deviceState > 0:
            result= True
        else:
            result= False
        return result

    """Retrieves information about devices registered in the catalog and selects only those "online" and updated in the last 12 hours """
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
            current_time=time.time()
            dev_online = [device for device in result if device["Online"]
                         and (current_time - device['lastUpdate']) < 12 * 3600]
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
    If the considered device is switched on, then it retrieves the metadata_id of the power measurement for that device."""
    def selectMetaHAIDs(self,houseID):
        house_devices= self.getHouseDevList(houseID)
        devices_list=[]
        selectedMetaHAIDs=[] 
        for element in house_devices:
            devices_list.append(element[1])        
        for dev_id in devices_list:
            meta_data = self.client.getMetaHAIDs(dev_id)
            to_retrieve = ['left_plug', 'center_plug', 'right_plug']
            switch_metaIDs = []
            for item in meta_data:
                if item in to_retrieve:
                    switch_metaIDs.append(meta_data[item])
            deviceState= self.getswitchesStates(switch_metaIDs)      
            if deviceState:
                metaHAID=meta_data['power']
                selectedMetaHAIDs.append(metaHAID)
        return selectedMetaHAIDs
    
    """Returns the last power reading for each selected device in the house"""
    def getlastPower(self,houseID):
        try:
            selectedMetaHAIDs=self.selectMetaHAIDs(houseID)
            query = """SELECT metadata_id, state, MAX(last_updated_ts) AS max_timestamp
                        FROM states
                        WHERE metadata_id IN ({})
                        """.format(','.join('?' for _ in selectedMetaHAIDs))
            self.HADBCur.execute(query,selectedMetaHAIDs)
            rows = self.HADBCur.fetchall()        
            df = pd.DataFrame(rows, columns=['metadata_id','power', 'last_update'])
            if(str(df['power']).replace(".", "").replace("-", "").isnumeric()):
                df['power'] = df['power'].astype(float)
            else:
                df['power'] = 0.0
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        return df
        
    """Computes the power recorded for a specific house (sum of the power recorded by the devices)."""
    def computeTotalPower(self,houseID):
        data_df = self.getlastPower(houseID)  
        totalpower=data_df['power'].sum()    
        return totalpower
        
    """Returns the allowed power limit value for a specific house."""
    def getPowerLimitHouse (self,houseID):
        try: 
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "HouseSettings", "keyName": "houseID", "keyValue": houseID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)
            power_limit=result[0]["powerLimit"]
            return power_limit
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)   
            
    """Checks for blackouts. If the power recorded exceeds the allowed limit value, then you must turn off a device."""    
    def controlPower(self,houseID):
        total_power = self.computeTotalPower(houseID)
        house_limit = self.getPowerLimitHouse(houseID)
        if total_power > house_limit:
            self.myMQTTfunction(houseID)

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

    """Retrieves information about a specific device"""
    def getDeviceInfo(self, deviceID, verbose = False):
        try:
            result = self.getCatalogInfo("Devices", "deviceID", deviceID, verbose=verbose)

            return result
        except HTTPError as e:
            raise e

    """Retrieves information about a specific house"""
    def getHouseInfo(self,houseID):
        try:
            result = self.getCatalogInfo("Houses", "houseID", houseID)

            return result[0]
        except HTTPError as e:
            raise e

    """Finds the device with the last updated highest power consumption in the house and turns it off"""
    def myMQTTfunction(self, houseID):
        lastReadings = self.getlastPower(houseID)
        row = lastReadings.loc[lastReadings["power"].idxmax()]
        metaHAID = row["metadata_id"]
        deviceID=self.getDeviceID(metaHAID)
        topic = "smartSocket/control"
        msg = {
        "deviceID" : deviceID, 
        "states" : [0,0,0]
        }
        str_msg = json.dumps(msg, indent=2)
        self.client.MQTT.Publish(topic, str_msg, talk=False)
        print("House %s power consumption exceeded limit, device %s was turned off" % (houseID,deviceID))
        house = self.getHouseInfo(houseID)
        device = self.getDeviceInfo(deviceID)
        msg = {
            "title" : "House %s power consumption exceeded limit" % house["houseName"],
            "message" : "Device %s was turned off" % device["deviceName"]
        }
        self.client.MQTT.notifyHA(msg, talk = True)
    
    """Controls for each house"""
    def controlPowerforall(self):
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
                self.controlPower(houseID)
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        

if __name__ == "__main__":
    MPC = maxPowerControl()
