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

            testDB_loc = "testDB.db"
            if(not IN_DOCKER):
                testDB_loc = "maxPowerControl/" + testDB_loc
            else:
                testDB_loc = "HomeAssistant/testDB.db" #da aggiornare poi con home assistant
            self.HADBConn = sqlite3.connect(testDB_loc)
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
            

    """
    Returns the last power reading for each device in the house
    """
    def getlastPower(self,houseID):
        try:
            query1="SELECT\
                    CASE \
                        WHEN entity_id = 'sensor.power' THEN 'D1'\
                        ELSE 'D' || SUBSTR(entity_id, LENGTH('sensor.power_') + 1, LENGTH(entity_id) - LENGTH('sensor.power_'))\
                    END AS deviceID,state, MAX(strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch'))) as last_updated\
                    FROM states1\
                    WHERE entity_id LIKE 'sensor.power%'\
                    GROUP BY deviceID"
            self.HADBCur.execute(query1)
            rows1 = self.HADBCur.fetchall()
        except HTTPError as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from HomeAssistant DB " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        combined_results = []

        houses_devs_list = self.getHouseDevList()
        for row1 in rows1:
            deviceID = row1[0]
            power = row1[1]
            timestamp= row1[2]
            for row2 in houses_devs_list:
                if row2[1] == deviceID:
                    houseID = row2[0]
                    combined_results.append((houseID, deviceID,power,timestamp))
        return combined_results
    
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

    def loadLastPowerDataHouse(self,houseID):
        data = self.getlastPower(houseID)      
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
        try: 
            catalogAddress = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "HouseSettings", "keyName": "houseID", "keyValue": houseID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)
            return result[0]["powerLimit"]
        except HTTPError as e:
            message = "An error occurred while retriving info from catalog " + e._message
            raise HTTPError(status=e.status, message=message)
        except Exception as e:
            message = "An error occurred while retriving info from catalog " + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)   
        
    '''def getLastUpdate(self,houseID):
        query="SELECT Devices.deviceID, max(Devices.lastUpdate) as lastUpdate,Online\
               FROM Devices,HouseDev_conn\
               WHERE Devices.deviceID=HouseDev_conn.deviceID and houseID=? and online='1'"
        self.catalogCures.execute(query,(houseID,))
        rows = self.catalogCures.fetchall()
        return rows     
    
    def controlLastUpdateDevice(self,houseID):    
        data = self.getLastUpdate(houseID)
        df = pd.DataFrame(data, columns=['deviceID','lastUpdate','status'])
        devicetoOFF = df['deviceID'].values[0]
        return devicetoOFF 
    '''       
        
    def controlPower(self,houseID):
        if self.computeTotalPower(houseID)>self.getPowerLimitHouse(houseID):
            self.myMQTTfunction(houseID)

    """
    Finds the device with the last updated highest power consumption in the house and turns it off 
    """
    def myMQTTfunction(self, houseID):
        lastReadings = self.loadLastPowerDataHouse(houseID)
        row = lastReadings.loc[lastReadings["power"].idxmax()]
        deviceID = row["deviceID"]
        topic = "/smartSocket/control"
        msg = {
        "deviceID" : deviceID, 
        "states" : [0,0,0]
        }
        str_msg = json.dumps(msg, indent=2)
        self.client.MQTT.Publish(topic, str_msg, talk=False)
        print("House %s power consumption exceeded limit, device %s was turned off" % (houseID,deviceID))
        msg = {
            "title" : ("House %s power consumption exceeded limit", houseID),
            "message" : ("Device %s was turned off", deviceID)
        }
        self.client.MQTT.notifyHA(msg, talk = True)

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
