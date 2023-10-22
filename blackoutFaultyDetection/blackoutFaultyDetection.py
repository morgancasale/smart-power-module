import os
import time
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
import sqlite3


class blackoutAndFaulty():
    def __init__(self):
        
        # uk range
        self.v_upper_bound=253
        self.v_lower_bound=216
        #how many measures should be incorrect to consider a blackout
        self.blackout_lim = 5 #dispositivi
        self.faultyLim = 1 #misure   

        config_file = "blackoutFaultyDetection.json"
        if(not IN_DOCKER):
            config_file = "blackoutFaultyDetection/" + config_file

        self.client = ServiceBase(config_file)
        self.client.start()

        while(True):
            try:
                self.controlAndDisconnect()
                time.sleep(4)
            except HTTPError as e:
                message = "An error occurred running the Blackout and Fault detection service: " + e._message
                raise Exception(message)
            except Exception as e:
                message = "An error occurred running the Blackout and Fault detection service: " + str(e)
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
    
    def lastValueCheck(self, HAID):
        meta = self.client.getMetaHAIDs(HAID)
        voltageID=meta["voltage"]
        powerID=meta["power"]
        
        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT metadata_id, MAX(last_updated_ts), state
            FROM {}
            WHERE metadata_id
            = ?""".format(self.database),(powerID,))
        result = self.curHA.fetchone()[2]

        if result !='unknown' and result !='unavailable':
            power = float(result)
        else:
            power = None
        
        self.curHA.execute("""
            SELECT metadata_id, MAX(last_updated_ts), state
            FROM {}
            WHERE metadata_id
            = ?""".format(self.database),(voltageID,))
        result = self.curHA.fetchone()[2]
        if result !='unknown' and result !='unavailable':

            voltage = float(result)
        else:
            voltage = None

        return {"power": power, "voltage": voltage} 
        #[ID, power, time], [id, voltage, time]
        
    def prevValuesCheck(self, ID):
    # Retrieve the 10 largest values of the timestamp column for the given moduleID
        meta = self.client.getMetaHAIDs(ID)
        powerID=meta["power"]
        self.curHA.execute("""
            SELECT state FROM (
                SELECT state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE metadata_id = ?
            )
            WHERE row_num <= 2 """.format(self.database), (powerID,))
        results_power = self.curHA.fetchall()
        
        voltageID=meta["voltage"]
        self.curHA.execute("""
            SELECT  state FROM (
                SELECT  state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE metadata_id = ?
            )
            WHERE row_num <= 2 """.format(self.database), (voltageID,))
        results_voltage = self.curHA.fetchall()
        
        
        #for result in results:
        #     print(f"ID: {result[0]}, timestamp: {result[1]}")
        return results_voltage, results_power

    
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
    


    def onlineTimeCheck(self, id):
        result = self.getDeviceInfo(id)
        last_update = result[0]["lastUpdate"]
        current_time = time.time()

        time_difference = current_time - last_update

        if time_difference > 43200:  # 12 hours in seconds
            return False
        else:
            return True

        
        
    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider_faulty=[]
        to_consider_bl=[]
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
                    to_consider_bl.append(house_module)
                    settings = self.getDeviceSettingsInfo(house_module)[0]
                    if(settings["HPMode"] == 1 and settings["FBControl"] == 1):
                        to_consider_faulty.append(house_module)
        return to_consider_faulty, to_consider_bl
        
    def getApplianceInfo(self, applianceType, verbose = False):
        try:
            result = self.getCatalogInfo("AppliancesInfo", "applianceType", applianceType, verbose=verbose)

            return result
        except HTTPError as e:
            raise e

    def getRange(self, deviceID):   

        device_type = self.getDeviceSettingsInfo(deviceID)[0]["applianceType"]
        if device_type == "None":
            return None

        dev_range = self.getApplianceInfo(device_type)[0][0]
        if dev_range is not None:
            return dev_range
        else:
            return None
    
    def blackOutRangeCheck(self, volt_meausure):
        if (self.v_lower_bound < int(volt_meausure) < self.v_upper_bound):
            return False
        else: return True

    def faultyCheck(self, appl_info, last_meas, ID, single_or_mult):
        
    
        if single_or_mult=='s':
            funct_min = appl_info["functioningRangeMin"]
            funct_max = appl_info["functioningRangeMax"]
        
            is_not_faulty = int(last_meas["power"]) >= 0
            is_not_faulty &= (funct_min < int(last_meas["power"]) < funct_max)
            is_not_faulty &= (self.v_lower_bound < int(last_meas["voltage"]) < self.v_upper_bound)
        
        else: 
            funct_min = appl_info["functioningRangeMin"]
            funct_max = appl_info["functioningRangeMax"]
            is_not_faulty = int(last_meas["power"][0]) >= 0
            is_not_faulty &= (funct_min < int(last_meas["power"][0]) < funct_max)
            is_not_faulty &= (self.v_lower_bound < int(last_meas["voltage"][0]) < self.v_upper_bound)
            
        return not is_not_faulty
    
    def retrieveSocket(self,ID):
        switches = self.getDeviceSettingsInfo(ID)[0]["enabledSockets"]
        return switches
        
    def MQTTInterface(self, ID, case):
        topic = "/smartSocket/control"
        settings = self.getDeviceSettingsInfo(ID)[0]
        device = self.getDeviceInfo(ID)[0]
        if case == 'f' and settings["FBMode"]=="Notify" :
            msg= {
            "deviceID" : ID, 
            "states" : [0,0,0]
            }

            notifyMsg = {
                "title": "Faulty device",
                "message": "The appliance connected to module %s seems to not be working properly." % device["deviceName"]
            }            
            self.client.MQTT.notifyHA(notifyMsg)
        elif case == 'f' and settings["FBMode"]=="Turn OFF":   
            msg= {
            "deviceID" : ID, 
            "states" : [0,0,0]
            }

            notifyMsg = {
                "title": "Faulty device",
                "message": 
                """The appliance connected to module %s seems to not be working properly, 
                turning OFF module.""" % device["deviceName"]
            }
            self.client.MQTT.notifyHA(notifyMsg)

            str_msg = json.dumps(msg, indent=2)
            self.client.MQTT.Publish(topic, str_msg, talk=False)
        else:
            msg= {
            "deviceID" : '*', 
            "states" : [0,0,0]
            }
            notifyMsg = {
                "title": "Incoming blackout detected!",
                "message": "Turning OFF all modules."
            }
            self.client.MQTT.notifyHA(notifyMsg)
            
            str_msg = json.dumps(msg, indent=2)
            self.client.MQTT.Publish(topic, str_msg, talk=False)
        
    def getHouseList(self):
        result = self.getCatalogInfo("Houses", "houseID", "*")

        house_list = [row["houseID"] for row in result]
        if not type(house_list) is list:
            house_list = [house_list]
        return house_list

    #if there is a blackout, all the devices are disconnected and they're put offline-->we din't check anymore
    def controlAndDisconnect(self):
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
            blackout_cont = 0
            modules_faulty, modules_bl =  self.houseInfo(house)
            if modules_bl is not None:
                for module in modules_bl:
                    faulty_cont = 0
                    value = self.getRange(module) #info[i][0] = ID
                    last_measurement = self.lastValueCheck(module)#[power, voltage]
                    if last_measurement["voltage"] != None :
                        if self.blackOutRangeCheck(last_measurement["voltage"]) :
                            blackout_cont += 1 
                        if blackout_cont > self.blackout_lim:
                            print('Predicted blackout in house %s', house)
                            self.MQTTInterface(module, 'b')
                            break
                        if module in modules_faulty and last_measurement['power']!=None and value != None:
                            if self.faultyCheck(value, last_measurement, module,'s'):
                                prevVoltage, prevPower = self.prevValuesCheck(module)
                                readings = list(zip(prevVoltage, prevPower))
                                for reading in readings:
                                    r = {"voltage": reading[0], "power": reading[1]}
                                    if self.faultyCheck(value, r, module,'m'):
                                        faulty_cont += 1   
                                        if faulty_cont >= self.faultyLim:
                                            print("Device with ID " + module + " is faulty!")
                                            self.MQTTInterface( module, 'f')
                                            break
        self.connHA.close()
                                    

if __name__ == "__main__":
    service = blackoutAndFaulty()
