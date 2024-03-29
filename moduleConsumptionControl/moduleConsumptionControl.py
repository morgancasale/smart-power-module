import os
import time
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
import sqlite3


class ModuleConsumptionControl():

    def __init__(self):
        try:
            config_file = "moduleConsumptionControl.json"
            if(not IN_DOCKER):
                config_file = "moduleConsumptionControl/" + config_file

            self.client = ServiceBase(config_file)
            self.client.start()

            while(True): 
                self.control()
                time.sleep(2)
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

    def lastValueCheck(self, ID):
        meta = self.client.getMetaHAIDs(ID)
        powerID=meta["voltage"]

        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT metadata_id, MAX(last_updated_ts), state
            FROM {}
            WHERE metadata_id
            = ?""".format(self.database),(powerID,))
        result = self.curHA.fetchone()[2]

        if result !='unknown' and result !='unavailable':
            return float(result)
        else:
            return None 
            
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
    
    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider=[]
        house_modules = self.getHouseDevList(house_ID)
        for house_module in house_modules :
            meta = self.client.getMetaHAIDs(house_module)
            switch_metaIDs = []
            switch_metaIDs.extend([meta["left_plug"], meta["right_plug"], meta["center_plug"]])
            result = self.getDeviceInfo(house_module)
            update_check= self.onlineTimeCheck(house_module)
            moduleState= self.getSwitchesStates(switch_metaIDs)
            if moduleState:
                if (result[0]["Online"] & update_check) :
                    settings = self.getDeviceSettingsInfo(house_module)[0]
                    if(settings["HPMode"] == 1 and settings["MPControl"] == 1):
                        to_consider.append(house_module)
            return to_consider  
        
    def getApplianceInfo(self, applianceType, verbose = False):
        try:
            result = self.getCatalogInfo("AppliancesInfo", "applianceType", applianceType, verbose=verbose)

            return result
        except HTTPError as e:
            raise e 
        
    def getRange(self, ID):
        maxPower = self.getDeviceSettingsInfo(ID)[0]["maxPower"]
        if maxPower != None:
            return maxPower
        else:
            return None
            
    def MQTTInterface(self, ID):
        settings = self.getDeviceSettingsInfo(ID)[0]
        device = self.getDeviceInfo(ID)[0]
        notifyMsg = {
            "title": "Module power threshold exceeded",
            "message": "The consumption of the appliance connected to module %s has exceeded the selected threshold" % device["deviceName"]
        }
        
        if settings["MPMode"] != "Notify" : 
            self.MQTTInterface(ID)
            topic="smartSocket/control"
            msg = {
                "deviceID" : ID, 
                "states" : [0,0,0]
                }
            
            notifyMsg["message"] += ",\n turning OFF module"

            str_msg = json.dumps(msg, indent=2)
            self.client.MQTT.Publish(topic, str_msg)

        notifyMsg["message"] += "."
        self.client.MQTT.notifyHA(notifyMsg)        
            
    def getHouseList(self):
        result = self.getCatalogInfo("Houses", "houseID", "*")

        house_list = [row["houseID"] for row in result]
        if not type(house_list) is list:
            house_list = [house_list]
        return house_list
    
    def onlineTimeCheck(self, id):
        result = self.getDeviceInfo(id)
        last_update = result[0]["lastUpdate"]
        current_time = time.time()

        time_difference = current_time - last_update

        if time_difference > 43200:  # 12 hours in seconds
            return False
        else:
            return True
    
    def control(self):
        HADB_loc = "HADB.db"
        HADB_loc = "homeAssistant/HADB/" + HADB_loc

        self.connHA = sqlite3.connect(HADB_loc)
        self.curHA = self.connHA.cursor()
        self.database = 'states'
        self.onlineDev ='Devices'  # online
        self.ranges ='AppliancesInfo'  #ranges
        self.devices_settings = 'DeviceSettings' #deviceID,enabledSockets,parControl 
        self.housesdev ='HouseDev_conn' #Device per house
        self.houses = 'Houses' #house ID

        houses = self.getHouseList()
        for house in houses:
            modules = self.houseInfo(house)
            if(modules != None):
                for module in modules:
                    value = self.getRange(module) #info[i][0] = ID
                    last_measurement = self.lastValueCheck(module)#[id, time,power]
                    if  last_measurement != None:
                        if int(last_measurement)> value:
                            self.MQTTInterface(module)
        self.connHA.close()
                                


if __name__ == "__main__":
    control = ModuleConsumptionControl()





