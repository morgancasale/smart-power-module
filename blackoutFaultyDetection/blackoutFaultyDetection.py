
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
        self.blackout_lim = 5
        self.faultyLim = 0

        config_file = "blackoutFaultyDetection.json"
        if(not IN_DOCKER):
            config_file = "blackoutFaultyDetection/" + config_file

        self.client = ServiceBase(config_file)
        self.client.start()

        while(True):
            try:
                self.controlAndDisconnect()
                time.sleep(2)
            except HTTPError as e:
                raise HTTPError(status=e.status, message ="An error occurred running the Blackout and Fault detection service: " + e._message)
            except Exception as e:
                raise Server_Error_Handler.InternalServerError(message="An error occurred running the Blackout and Fault detection service: " + str(e))

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

    def PrevValuesCheck(self, HAID):
        # Retrieve the N largest values of the timestamp column for the given moduleID
        powerStateID= 'sensor.voltage' + HAID
        voltageStateID= 'sensor.power' + HAID
        self.curHA.execute("""
            SELECT entity_id, last_updated_ts, state FROM (
                SELECT entity_id,last_updated_ts, state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE entity_id = ?
            )
            WHERE row_num <= 5 """.format(self.database), (powerStateID,))
        result = self.curHA.fetchall()
        if result is None:
            power = [None]
        else:
            power = [float(row[2]) for row in result]

        self.curHA.execute("""
            SELECT entity_id, last_updated_ts, state FROM (
                SELECT entity_id, last_updated_ts, state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE entity_id = ?
            )
            WHERE row_num <= 5 """.format(self.database), (voltageStateID,))
        result = self.curHA.fetchall()
        if result is None:
            voltage = [None]
        else:
            voltage = [float(row[2]) for row in result]

        return power, voltage
    
    def lastValueCheck(self, HAID):
        powerStateID = 'sensor.power' + HAID
        voltageStateID = 'sensor.voltage' + HAID
        
        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(powerStateID,))
        result = self.curHA.fetchone()[2]

        if result is not None:
            power = float(result)
        else:
            power = None
        
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(voltageStateID,))
        result = self.curHA.fetchone()[2]
        if result is not None:
            voltage = float(result)
        else:
            voltage = None

        return {"power": power, "voltage": voltage} 
        #[ID, power, time], [id, voltage, time]
    
    '''    
    def moduleInfo(self):
        #this method retrieves the status of the module, if the module is off
        #there is no need to check for standBy power
        self.Res#Cur.execute("""SELECT *
                        FROM {}""".format(self.modules_and_switches))
        result = self.Res#Cur.fetchall()
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
                if(settings["HPMode"] == 1 and settings["faultControl"] == 1):
                    to_consider.append(house_module)
        if len(to_consider) > 0:
            return to_consider
        else: return None   
        
    def getApplianceInfo(self, applianceType, verbose = False):
        try:
            result = self.getCatalogInfo("AppliancesInfo", "applianceType", applianceType, verbose=verbose)

            return result
        except HTTPError as e:
            raise e

    def getRange(self, deviceID):   
        device_type = self.getDeviceSettingsInfo(deviceID)[0]["applianceType"]
        dev_range = self.getApplianceInfo(device_type)[0][0]
        if dev_range is not None:
            return dev_range
        else:
            return None
    
    def blackOutRangeCheck(self, volt_meausure):
        if (self.v_lower_bound < int(volt_meausure) < self.v_upper_bound):
            return False
        else: return True

    def faultyCheck(self, appl_info, last_meas, ID):
        faulty_control = self.getDeviceSettingsInfo(ID)[0]["faultControl"]

        if not faulty_control: #if faulty control is disabled
            return False
        else:
            funct_min = appl_info["functioningRangeMin"]
            funct_max = appl_info["functioningRangeMax"]
            
            is_not_faulty = int(last_meas["power"]) >= 0
            is_not_faulty &= (funct_min < int(last_meas["power"]) < funct_max)
            is_not_faulty &= (self.v_lower_bound < int(last_meas["voltage"]) < self.v_upper_bound)
           
            return not is_not_faulty
    
    def retrieveSensorData(self, ID):
        if(self.client.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
            partial = self.client.getHAID(ID)
        else:
            partial = "_"+ID[1:]
        powerStateID= 'sensor.voltage' + partial
        voltageStateID= 'sensor.power' + partial
        energyStateID = 'sensor.energy' + partial
        currentStateID = 'sensor.current' + partial

        queries = [
        voltageStateID,
        currentStateID,
        powerStateID,
        energyStateID]
        
        sensor_data = []
    
        for entity_id in queries:
            print(entity_id)
            query = f"""
            SELECT MAX(last_updated_ts), state
            FROM {self.database}
            WHERE entity_id = ?
            """
            self.curHA.execute(query, (entity_id,))
            result = self.curHA.fetchone()
            sensor_data.append(result[1])
        return sensor_data #[voltage, current,power,  energy]
    
    def retrieveSocket(self,ID):
        switches = self.getDeviceSettingsInfo(ID)[0]["enabledSockets"]
        return switches
        
    def MQTTInterface(self, ID, case):
        self.client.start()
        topic = "/smartSocket/control"
        if case == 'f':
            msg= {
            "deviceID" : ID, 
            "states" : [0,0,0]
            }
        else:   
            msg= {
            "deviceID" : '*', 
            "states" : [0,0,0]
            }
        
        str_msg = json.dumps(msg, indent=2)

        self.client.MQTT.Publish(topic, str_msg, talk=False)
        self.client.MQTT.stop() 
        
    def getHouseList(self):
        result = self.getCatalogInfo("Houses", "houseID", "*")

        house_list = [row["houseID"] for row in result]
        if not type(house_list) is list:
            house_list = [house_list]
        return house_list

    #if there is a blackout, all the devices are disconnected and they're put offline-->we din't check anymore
    def controlAndDisconnect(self):
        HADB_loc = "testDB.db" #TODO : Da aggiornare poi con home assistant
        if(not IN_DOCKER):
            HADB_loc = "maxPowerControl/" + HADB_loc
        else:
            HADB_loc = "HomeAssistant/" + HADB_loc

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
            modules =  self.houseInfo(house)
            if modules is not None:
                for module in modules:
                    HAID = self.getHAID(module)
                    faulty_cont = 0
                    value = self.getRange(module) #info[i][0] = ID
                    last_measurement = self.lastValueCheck(HAID)#[power, voltage]
                    if last_measurement["voltage"] != None and value != None :
                        if self.blackOutRangeCheck(last_measurement["voltage"]) :
                            blackout_cont += 1 
                        if blackout_cont > self.blackout_lim:
                            print('Predicted blackout in house %s', house)
                            self.MQTTInterface(module, 'b')
                            break
                        if self.faultyCheck(value, last_measurement, module):
                            prevVoltage, prevPower = self.PrevValuesCheck(HAID)
                            readings = list(zip(prevVoltage, prevPower))
                            for reading in readings:
                                r = {"voltage": reading[0], "power": reading[1]}
                                if self.faultyCheck(value, r, module):
                                    faulty_cont += 1   
                                    if faulty_cont >= self.faultyLim:
                                        print("Device with ID " + module + " is faulty!")
                                        self.MQTTInterface( module, 'f')
                                        break
        self.connHA.close()
                                    

if __name__ == "__main__":
    service = blackoutAndFaulty()
