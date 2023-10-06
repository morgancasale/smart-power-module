import os
import time
import sys
import sqlite3

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *


class StandByPowerDetection():

    def __init__(self):
        try:
            config_file = "standByPowerDetection.json"
            if(not IN_DOCKER):
                config_file = "standByPowerDetection/" + config_file
            self.client = ServiceBase(config_file)

            self.client.start()
        
            while(True):
                self.controlAndDisconnect() 
                time.sleep(120)
        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise Exception(message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Exception(message)

    def prevValuesCheck(self, ID):
        # Retrieve the 10 largest values of the timestamp column for the given moduleID
        meta = self.client.getMetaHAIDs(ID)
        powerID=meta["power"]
        self.curHA.execute("""
            SELECT entity_id, state FROM (
                SELECT entity_id, state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE entity_id = ?
            )
            WHERE row_num <= 60 """.format(self.database), (powerID,))
        results = self.curHA.fetchall()
        
        
        #for result in results:
        #     print(f"ID: {result[0]}, timestamp: {result[1]}")
        return results

    def lastValueCheck(self, ID):
        meta = self.client.getMetaHAIDs(ID)
        powerID=meta["power"]
        #return [(ID, max_timestamp, power)]
        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(powerID,))
        results = self.curHA.fetchone()
        if results is not None:
            return (results)
        else:
            return None   
    

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
        
    def getHouseDevList(self, houseID="*"):
        try:
            result = self.getCatalogInfo("HouseDev_conn", "houseID", houseID)

            house_dev_list = []
            for row in result:
                house_dev_list.append(row["deviceID"])
            return house_dev_list
        except HTTPError as e:
            raise e

    def getDeviceInfo(self, deviceID, verbose = False):
        try:
            result = self.getCatalogInfo("Devices", "deviceID", deviceID, verbose=verbose)

            return result
        except HTTPError as e:
            raise e
        
    def getDeviceSettingsInfo(self, deviceID, verbose = False):
        try:
            result = self.getCatalogInfo("DeviceSettings", "deviceID", deviceID, verbose=verbose)

            return result
        except HTTPError as e:
            raise e
        
    def getApplianceInfo(self, applianceType, verbose = False):
        try:
            result = self.getCatalogInfo("AppliancesInfo", "applianceType", applianceType, verbose=verbose)

            return result
        except HTTPError as e:
            raise e

    def houseInfo(self, house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider=[]
        house_modules = self.getHouseDevList(house_ID)
        for house_module in house_modules :
            meta = self.client.getMetaHAIDs(house_module)
            switch_metaIDs = []
            switch_metaIDs.extend([meta["left_plug"], meta["right_plug"], meta["center_plug"]])
            result = self.getDeviceInfo(house_module)
            moduleState= self.getSwitchesStates(switch_metaIDs)
            if moduleState:
                if (result[0]["Online"]) :
                    settings = self.getDeviceSettingsInfo(house_module)[0]
                    if(settings["HPMode"] == 1 and settings["parControl"] == 1):
                        to_consider.append(house_module)
            return to_consider 
        
    def getRange(self, ID):
        settings = self.getDeviceSettingsInfo(ID)[0]
        if settings["parMode"] == "Manual" :
            result=settings["parThreshold"]
        else:
            device_type = self.getDeviceSettingsInfo(ID)[0]["applianceType"]
            result = self.getApplianceInfo(device_type)[0][0]["standByPowerMax"]
        if result is not None:
            dev_range = result
            return dev_range
        else:
            return None
            
    
    def MQTTInterface(self, ID):
        self.client.start()
        topic="/smartSocket/data"
        #socket= self.retrieveSocket(ID)
        #socket_states =  [-1 if item == '0' else 0 for item in socket]
        #print(socket_states)
        msg= {
            "deviceID" : ID, 
            "states" : [0,0,0]
            }
        str_msg = json.dumps(msg, indent=2)
        notifyMsg=("The consumption of the appliance connected to %s is parasitic" % ID)
        self.client.notifyHA(notifyMsg)
        self.client.MQTT.Publish(topic, str_msg)
        self.client.MQTT.stop() 

    def getHouseList(self):
        result = self.getCatalogInfo("Houses", "houseID", "*")

        house_list = [row["houseID"] for row in result]
        if not type(house_list) is list:
            house_list = [house_list]
        return house_list


    def getSwitchesStates(self, ID_list):
            stateList=[]
            for element in ID_list:
                self.curHA.execute("""
                    SELECT metadata_id, MAX(last_updated_ts)
                    FROM {}
                    WHERE metadata_id
                    = ?""".format(self.database),(element,))
                result=(self.curHA.fetchone()[0])
                if result == 'off':
                    result= 0
                else : result=1
                stateList.append(result)
            finalState= sum(stateList)
            if finalState > 0:
                res= True
            else:
                res= False
            return res

    def controlAndDisconnect(self):
        HADB_loc = "HADB.db" #TODO : Da aggiornare poi con home assistant
        if(not IN_DOCKER):
            HADB_loc = "homeAssistant/HADB/" + HADB_loc
        else:
            HADB_loc = "HomeAssistant/" + HADB_loc
        self.connHA = sqlite3.connect(HADB_loc)
        self.curHA = self.connHA.cursor()
        self.database = 'states'
        self.onlineDev ='Devices'  # online
        self.ranges ='AppliancesInfo'  #ranges
        self.devices_settings = 'DeviceSettings' #deviceID,enabledSockets,parControl 
        self.housesdev ='HouseDev_conn' #Device per houselast
        self.houses = 'Houses' #house ID

        house_list = self.getHouseList()
        
        for house in house_list:
            modules = self.houseInfo(house)
            if(modules is None):
                break
            for info in modules:
                standByPowercont=0 
                value = self.getRange(info) #info[i][0] = ID
                last_measurement = self.lastValueCheck(info)#[id, time,power]
                if last_measurement[2] != None and value != None :
                    if ((1 <= int(last_measurement[2]) <= int(value)) and last_measurement != 0):
                        prevRows= self.prevValuesCheck(info[0][0])
                        for prevValues in prevRows:
                            if (1<=int(prevValues[1])<=value):
                                standByPowercont+=1   
                            if standByPowercont>=5:
                                self.MQTTInterface(info[0][0])
                                

control = StandByPowerDetection()