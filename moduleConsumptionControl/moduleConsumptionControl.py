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
                self.controlAndNotify()
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

    def getHAID(self, moduleID):
        try:
            if(self.client.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
                partial = self.client.getHAID(moduleID)
            else:
                partial = "_" + moduleID[1:]
            return partial
        except HTTPError as e:
            raise e

    def prevValuesCheck(self, moduleID):
        # Retrieve the N largest values of the timestamp column for the given moduleID
        partial=moduleID[1:]
        powerStateID= 'sensor.power_' + partial
        self.curHA.execute("""
            SELECT entity_id, state FROM (
                SELECT entity_id, state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE entity_id = ?
            )
            WHERE row_num <= 5 """.format(self.database), (powerStateID,))
        results = self.curHA.fetchall()
        
        #for result in results:
        #    print(f"ID: {result[0]}, timestamp: {result[1]}")
        return results

    def lastValueCheck(self, HAID):
        powerStateID = 'sensor.power' + HAID

        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(powerStateID,))
        result = self.curHA.fetchone()[2]

        if result is not None:
            return float(result)
        else:
            return None 
    
    ''' 
    def moduleInfo(self):
        #this method retrieves the status of the module, if the module is off
        #there is no need to check for standBy power
        self.CatCu#r.execute("""SELECT *
                        FROM {}""".format(self.modules_and_switches))
        result = self.CatCu#r.fetchall()
        if result is not None:
            return (result)
        else:
            return None        
    '''
              
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

    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider=[]
        house_modules = self.getHouseDevList(house_ID)
        for house_module in house_modules :
            result = self.getDeviceInfo(house_module)
            if (result[0]["Online"]) :
                settings = self.getDeviceSettingsInfo(house_module)[0]
                if(settings["HPMode"] == 1 and settings["MPControl"] == 1):
                    to_consider.append(house_module)
        if len(to_consider) > 0:
            return to_consider
        else: return None   
        
    def getRange(self, ID):
        maxPower = self.getDeviceSettingsInfo(ID)[0]["maxPower"]
        if maxPower is not None:
            return maxPower
        else:
            return None
            
    def MQTTInterface(self, ID):
        self.client.start()
        topic="/smartSocket/control"
        msg= {
            "deviceID" : ID, 
            "states" : [0,0,0]
            }
        str_msg = json.dumps(msg, indent=2)
        self.client.MQTT.Publish(topic, str_msg)
        self.client.MQTT.stop()           
            
    def getHouseList(self):
        result = self.getCatalogInfo("Houses", "houseID", "*")

        house_list = [row["houseID"] for row in result]
        if not type(house_list) is list:
            house_list = [house_list]
        return house_list
    
    def controlAndNotify(self):
        HADB_loc = "testDB.db" #TODO : Da aggiornare poi con home assistant
        if(not IN_DOCKER):
            HADB_loc = "maxPowerControl/" + HADB_loc
        else:
            HADB_loc = "HomeAssistant/" + HADB_loc

        self.connHA = sqlite3.connect(HADB_loc)
        self.curHA= self.connHA.cursor()

        self.database= 'states'
        self.onlineDev='Devices'  # online
        self.onlinedev2 = 'DeviceResource_conn' #check Online for lastUpdate
        self.ranges='AppliancesInfo'  #ranges
        self.devices_settings= 'DeviceSettings' #deviceID,enabledSockets,parControl 
        self.housesdev='HouseDev_conn' #Device per house
        self.houses= 'Houses' #house ID

        houses = self.getHouseList()
        for house in houses:
            modules = self.houseInfo(house)
            if(modules is not None):
                for module in modules:
                    HAID = self.getHAID(module)
                    value = self.getRange(module) #info[i][0] = ID
                    last_measurement = self.lastValueCheck(HAID)#[id, time,power]
                    if  last_measurement != None:
                        if int(last_measurement)> value:
                            self.MQTTInterface(module)
        self.connHA.close()
                                


if __name__ == "__main__":
    control = ModuleConsumptionControl()





