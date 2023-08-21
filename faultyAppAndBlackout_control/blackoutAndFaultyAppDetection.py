
import os
import time
import sys

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
        self.blackout_lim=5
        self.faultyLim=5

        self.client= ServiceBase("C:/Users/mirip/Desktop/progetto_IOT/smart-power-module/faultyAppAndBlackout_control/serviceConfig_blackout_faulty.json")



    def PrevValuesCheck(self, moduleID):
        # Retrieve the N largest values of the timestamp column for the given moduleID
        partial=moduleID[1:]
        powerStateID= 'sensor.voltage_' + partial
        voltageStateID= 'sensor.power_' + partial
        self.curHA.execute("""
            SELECT entity_id, last_updated_ts, state FROM (
                SELECT entity_id,last_updated_ts, state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE entity_id = ?
            )
            WHERE row_num <= 5 """.format(self.database), (powerStateID,))
        power = self.curHA.fetchall()

        self.curHA.execute("""
            SELECT entity_id, last_updated_ts, state FROM (
                SELECT entity_id, last_updated_ts, state, ROW_NUMBER() 
                OVER (ORDER BY last_updated_ts DESC) AS row_num
                FROM {}
                WHERE entity_id = ?
            )
            WHERE row_num <= 5 """.format(self.database), (voltageStateID,))
        voltage = self.curHA.fetchall()
        return power, voltage
    
    def lastValueCheck(self, ID):
        partial=ID[1:]
        powerStateID= 'sensor.voltage_' + partial
        voltageStateID= 'sensor.power_' + partial
        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(powerStateID,))
        power = self.curHA.fetchone()
        
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(voltageStateID,))
        voltage= self.curHA.fetchone()
        return power, voltage 
        #[ID, power, time], [id, voltage, time]
    
        
    def moduleInfo(self):
        #this method retrieves the status of the module, if the module is off
        #there is no need to check for standBy power
        self.cur.execute("""SELECT *
                        FROM {}""".format(self.modules_and_switches))
        result = self.cur.fetchall()
        if result is not None:
            return (result)
        else:
            return None        
        
        
    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider=[]
        self.cur.execute("""SELECT deviceID
                        FROM {} 
                        WHERE houseID = ?""".format(self.housesdev),(house_ID,))
        house_modules= self.cur.fetchall()
        for house_module in house_modules :
            self.cur.execute("""SELECT deviceID, online
                            FROM {}
                            WHERE deviceID = ? """.format(self.onlineDev),(house_module))
            result = self.cur.fetchall()
            if (result[0][1]==1) : 
                self.cur.execute("""SELECT deviceID, enabledSockets, parControl
                                FROM {}
                                WHERE deviceID = ? """.format(self.devices_settings),(house_module))
                settings = self.cur.fetchall()
                if  (sum([int(x) for x in eval(settings[0][1])])>1):
                    print('ERRORE')
                    break
                if(settings[0][2] == 1) :
                    to_consider.append(result)
        if (to_consider) is not None:
            return (to_consider)
        else: return None   
        
    def getRange(self, ID):   
            self.cur.execute("""SELECT applianceType 
                            FROM {} 
                            WHERE deviceID
                            = ?""".format(self.devices_settings), (ID,))
            device_type = self.cur.fetchone()[0]
            self.cur.execute("""SELECT standByPowerMax, functioningRangeMin, functioningRangeMax
                            FROM {} 
                            WHERE applianceType
                            = ?""".format(self.ranges), (device_type,))
            dev_range = self.cur.fetchone()
            if dev_range is not None:
                return dev_range
            else:
                return None
    
    def blackOutRangeCheck(self, last_meas):
        if (self.v_lower_bound<int(last_meas[0][2])<self.v_upper_bound):
            return False
        else: return True

    def faultyCheck(self, range_value, last_meas, ID):
        self.cur.execute("""SELECT faultControl
                            FROM {} 
                            WHERE deviceID
                            = ?""".format(self.devices_settings), (ID,))
        faulty_control=self.cur.fetchone()[0]
        if not faulty_control:
            return False
        else:
            if (0<=int(last_meas[1][2])<range_value[0] or \
                range_value[1]<int(last_meas[1][2])<range_value[2] and\
                self.v_lower_bound<int(last_meas[0][2])<self.v_upper_bound):
                return False
            else: return True
    
    def retrieveSensorData(self, ID):
        partial = ID[1:]
        voltageStateID = 'sensor.voltage_' + partial
        powerStateID = 'sensor.power_' + partial
        energyStateID = 'sensor.energy_' + partial
        currentStateID = 'sensor.current_' + partial

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
        self.cur.execute("""SELECT enabledSockets
                            FROM {}
                            WHERE deviceID = ? """.format(self.devices_settings),(ID,))
        switches = self.cur.fetchone()[0]
        return switches
    
    def MQTTInterface(self, ID):
        self.client.start()
        topic="/smartSocket/data"
        sensor_data= self.retrieveSensorData(ID)
        socket= self.retrieveSocket(ID)
        msg=  {
            "deviceID": ID,# string
            "Voltage": sensor_data[0] , #float
            "Current": sensor_data[1], #float
            "Power": sensor_data[2],#float
            "Energy":  sensor_data[3],#float
            "SwitchStates":socket #[ "int", "int", "int"]
        }
    
        str_msg = json.dumps(msg, indent=2)

        self.client.MQTT.Publish(topic, str_msg)
        self.client.MQTT.stop()       
        
    def MQTTInterface(self, ID, case):
        self.client.start()
        topic = "/smartSocket/data"
        if case =='f':
            sensor_data= self.retrieveSensorData(ID)
            socket= self.retrieveSocket(ID)
            msg=  {
                "deviceID": ID,# string
                "Voltage": sensor_data[0] , #float
                "Current": sensor_data[1], #float
                "Power": sensor_data[2],#float
                "Energy":  sensor_data[3],#float
                "SwitchStates":socket #[ "int", "int", "int"]
            }
        else:  
            msg=  {
                        "deviceID": '*',
                        "Voltage": None,
                        "Current": None, 
                        "Power": None,
                        "Energy":  None,
                        "SwitchStates":None
                    }
        
        str_msg = json.dumps(msg, indent=2)

        self.client.MQTT.Publish(topic, str_msg)
        self.client.MQTT.stop() 
        

#if there is a blackout, all the devices are disconnected and they're put offline-->we din't check anymore
    def controlAndDisconnect(self):
        self.conn = sqlite3.connect('C:/Users/mirip/Desktop/IOT/lab4_es4/dbRC.sqlite')
        self.connHA = sqlite3.connect('C:/Users/mirip/Desktop/IOT/lab4_es4/testDB_Marika.db')
        self.cur = self.conn.cursor()
        self.curHA= self.connHA.cursor()
        self.database= 'states'
        self.onlineDev='Devices'  # online
        self.ranges='AppliancesInfo'  #ranges
        self.devices_settings= 'DeviceSettings' #deviceID,enabledSockets,parControl 
        self.housesdev='HouseDev_conn' #Device per house
        self.houses= 'Houses' #house ID
        self.cur.execute("""SELECT houseID
                    FROM {}""".format( self.houses))
        houses = self.cur.fetchall()
        for house in houses:
            blackout_cont=0
            modules=  self.houseInfo(house[0])
            for info in modules:
                faulty_cont=0
                value= self.getRange(info[0][0]) #info[i][0] = ID
                last_measurement= self.lastValueCheck(info[0][0])#[power, voltage]
                if last_measurement[0][2] != None and value!=None :
                    if self.blackOutRangeCheck(last_measurement) :
                            blackout_cont+=1 
                    if blackout_cont > self.blackout_lim:
                            print('blackout house', house)
                            self.MQTTInterface(house[0], info[0][0], 'b')
                            break
                    if self.faultyCheck(value, last_measurement, info[0][0]):
                        prevVoltage, prevPower=self.PrevValuesCheck(info[0][0])
                        res = list(zip(prevVoltage, prevPower))
                        for i in range(self.faultyLim):
                            if self.faultyCheck(value, res[i],info[0][0]):
                                faulty_cont+=1   
                                if faulty_cont>=self.faultyLim:
                                        print('faulty', info[0][0])
                                        self.MQTTInterface( info[0][0], 'f')
        self.conn.close()
        self.connHA.close()
                                    


control= blackoutAndFaulty()
while(True): 
    control.controlAndDisconnect()
    time.sleep(2)
