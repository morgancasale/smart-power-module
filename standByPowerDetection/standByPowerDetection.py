import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
from microserviceBase.serviceBase import *
import sqlite3

class StandByPowerDetection():

    def __init__(self):
        self.client= ServiceBase("C:/Users/mirip/Desktop/progetto_IOT/smart-power-module/standByPowerDetection/serviceConfig_example.json")
        
    
    def prevValuesCheck(self, moduleID):
        # Retrieve the 10 largest values of the timestamp column for the given moduleID
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
        #     print(f"ID: {result[0]}, timestamp: {result[1]}")
        return results

    def lastValueCheck(self, ID):
        partial=ID[1:]
        powerStateID= 'sensor.power_' + partial
        #return [(ID, max_timestamp, power)]
        #  retrieve the maximum value of timestamp column for each ID
        self.curHA.execute("""
            SELECT entity_id, MAX(last_updated_ts), state
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(powerStateID,))
        results = self.curHA.fetchone()
        if results is not None:
            return (results)
        else:
            return None   
    
        
    def moduleInfo(self):
        #this method retrieves the status of the module, if the module is off or offline(?)
        #there is no need to check for standBy power
        self.cur.execute("""SELECT *
                        FROM {}""".format(self.modules_and_switches))
        result = self.cur.fetchall()
        if result is not None:
            return (result)
        else:
            return None                
        
    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on
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
            self.cur.execute("""SELECT standByPowerMax
                            FROM {} 
                            WHERE applianceType
                            = ?""".format(self.ranges), (device_type,))
            result = self.cur.fetchone()
            if result is not None:
                dev_range = result[0]
                return dev_range
            else:
                return None
            
    
    def MQTTInterface(self, houseID, ID):
        self.client.start()
        '''self.cur.execute("""SELECT switchesStates
                            FROM {}
                            WHERE deviceID = ? """.format(self.modules_and_switches),(ID,))
        switches = self.cur.fetchone()[0]
        switches = ['1','0','1']'''
        topic="SmartModule/{}/dev/{}".format(houseID, ID)
        msg=  {
            "StandBy power consumption":{  
            "Active": {
            "Module": 0, #id
            #"Switches": switches
        }}}
    
        str_msg = json.dumps(msg, indent=2)

        self.client.MQTT.Publish(topic, str_msg)
        self.client.MQTT.stop() 

    def controlAndDisconnect(self):
        self.conn = sqlite3.connect('C:/Users/mirip/Desktop/IOT/lab4_es4/dbRC.sqlite')
        self.connHA = sqlite3.connect('C:/Users/mirip/Desktop/IOT/lab4_es4/testDB_Marika.db')
        self.cur = self.conn.cursor()
        self.curHA= self.connHA.cursor()
        self.database= 'states1'
        self.onlineDev='Devices'  # online
        self.ranges='AppliancesInfo'  #ok
        self.devices_settings= 'DeviceSettings' #deviceID,enabledSockets,parContorl 
        self.housesdev='HouseDev_conn' #Device per house
        self.houses= 'Houses' #ID
        self.cur.execute("""SELECT houseID
                    FROM {}""".format( self.houses))
        houses = self.cur.fetchall()
        for house in houses:
            modules=  self.houseInfo(house[0])
            for info in modules:
                standByPowercont=0 
                value= self.getRange(info[0][0]) #info[i][0] = ID
                last_measurement= self.lastValueCheck(info[0][0])#[id, time,power]
                if last_measurement[2] != None :
                    if (int(last_measurement[2])>=1 or int(last_measurement[2])<=value) and last_measurement!=0:
                        prevRows= self.prevValuesCheck(info[0][0])
                        for prevValues in prevRows:
                            if (int(prevValues[1])>=1 or int(prevValues[1])<=value):
                                standByPowercont+=1   
                            if standByPowercont>=5:
                                self.MQTTInterface(house[0], info[0][0])
                                


if __name__ == "__main__":
    control= StandByPowerDetection()
    control.controlAndDisconnect() 