import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
from microserviceBase.serviceBase import *
import sqlite3


class StandByPowerDetection():

    def __init__(self,database):
        self.conn = sqlite3.connect('C:/Users/hp/Desktop/IOT/lab4_es4/data_m.sqlite')
        self.cur = self.conn.cursor()
        self.database= 'data'
        self.modules_and_switches='Devices'
        self.ranges='AppliancesInfo'
        self.devices_db= 'Appliances'
        self.houses='HouseDev_conn'

    
    def prevValuesCheck(self, moduleID):
        # Retrieve the 10 largest values of the timestamp column for the given moduleID
        control.cur.execute("""
             SELECT deviceID, power FROM (
                 SELECT deviceID, power, ROW_NUMBER() 
                 OVER (ORDER BY timestamp DESC) AS row_num
                 FROM {}
                 WHERE deviceID = ?
             )
             WHERE row_num <= 10 """.format(self.database), (moduleID,))
        results = self.cur.fetchall()
        #for result in results:
        #    print(f"ID: {result[0]}, timestamp: {result[1]}")
        return results

       
    def lastValueCheck(self, ID):
        #return [(ID, max_timestamp, power)]
        #  retrieve the maximum value of timestamp column for each ID
        self.cur.execute("""
            SELECT deviceID, MAX(timestamp), power
            FROM {}
            WHERE deviceID
            = ?""".format(self.database),(ID,))
        results = self.cur.fetchone()
        
        return results
    
        
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
        #return true false?, come gestir errori
        
        
    def houseInfo(self,house_ID):
         #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider=[]
        self.cur.execute("""SELECT deviceID
                         FROM {} 
                         WHERE houseID = ?""".format(self.houses),(house_ID,))
        house_modules= self.cur.fetchall()
        for house_module in house_modules :
            self.cur.execute("""SELECT *
                             FROM {}
                             WHERE deviceID = ? """.format(self.modules_and_switches),(house_module))
            result = self.cur.fetchall()
            #if ( result[0][1] == 1 and sum(result[0][2:])==1):
            if (result[0][4]==1 and sum([int(x) for x in eval(result[0][5])])==1): 
                to_consider.append(result)
        if (to_consider) is not None:
            return (to_consider)
        else: return None    
        
    def getRange(self, ID):   
           self.cur.execute("""SELECT applianceType 
                            FROM {} 
                            WHERE deviceID
                            = ?""".format(self.devices_db), (ID,))
           device_type = self.cur.fetchone()[0]
           self.cur.execute("""SELECT standByPowerMax
                             FROM {} 
                             WHERE applianceType
                             = ?""".format(self.ranges), (device_type,))
           dev_range = self.cur.fetchone()[0]
           if dev_range is not None:
               return dev_range
           else:
               return None
            
    
    def MQTTStandByPowerInterface(self, houseID, ID):
        client= ServiceBase("C:/Users/hp/Desktop/IOT/lab4_es4/standbypower_control/serviceConfig_example.json")

        self.cur.execute("""SELECT switchesStates
                            FROM {}
                            WHERE deviceID = ? """.format(self.modules_and_switches),(ID,))
        switches = self.cur.fetchone()[0]
        topic="SmartModule/{}/dev/{}".format(houseID, ID)
        msg=  {
            "StandBy power consumption":{  
            "Active": {
            "Module": 0, 
            "Switches": switches
        }}}
        
        client.MQTT.start()
        client.MQTT.Subscribe(topic)
        client.MQTT.Publish(topic, msg)
        client.MQTT.stop() 

    def controlAndDisconnect(self):
        self.cur.execute("""SELECT DISTINCT houseID
                            FROM {}""".format( self.houses))
        houses = self.cur.fetchall()
        for house in houses:
            modules=  self.houseInfo(house[0])
            for info in modules:
                standByPowercont=0 
                value= self.getRange(info[0][0]) #info[i][0] = ID
                last_measurement= self.lastValueCheck(info[0][0])#[id, time,power]
                if (last_measurement[2]>=1 or last_measurement[2]<=value):
                    prevRows= self.prevValuesCheck(info[0][0])
                    for prevValues in prevRows:
                        if (prevValues[1]>=1 or prevValues[1]<=value):
                            standByPowercont+=1   
                        if standByPowercont>=4:
                            self.MQTTStandByPowerInterface(house[0], info[0][0])
                            break


if __name__ == "__main__":
    control= StandByPowerDetection('C:/Users/hp/Desktop/IOT/lab4_es4/data_m.sqlite')
    i=0
    while(i>3): 
        control.controlAndDisconnect()
        time.sleep(2)
       