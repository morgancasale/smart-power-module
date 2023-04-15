import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
import sqlite3
import time

class FaultyAppliancesDetection():

    def __init__(self,database):
        self.conn = sqlite3.connect('C:/Users/hp/Desktop/IOT/lab4_es4/data_m.sqlite')
        self.cur = self.conn.cursor()
        self.database= 'data'
        self.modules_and_switches='Devices'
        self.ranges='AppliancesInfo'
        self.devices_db= 'Appliances'
        self.v_upper_bound=253
        self.v_lower_bound=216
        self.blackout_lim=1
        self.houses='HouseDev_conn'

        self.clientID="provamqttprogetto0"
        self.broker="mqtt.eclipseprojects.io"

    def prevValuesCheck(self, moduleID):
        # Retrieve the 10 largest values of the timestamp column for the given moduleID
        self.cur.execute("""
            SELECT deviceID, power, voltage FROM (
                SELECT deviceID, power, voltage, ROW_NUMBER() 
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
            SELECT deviceID, MAX(timestamp), power,  voltage
            FROM {}
            WHERE deviceID
            =?""".format(self.database),(ID,))
        results = self.cur.fetchone()
        
        return results
        
    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device connected to them
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
        self.cur.execute("""SELECT standByPowerMax, functioningRangeMin, functioningRangeMax
                          FROM {} 
                          WHERE applianceType
                          = ?""".format(self.ranges), (device_type,))
        dev_range = self.cur.fetchall()
        if dev_range is not None:
            return dev_range
        else:
            return None

    def faultyRangeCheck(self, range_value, last_meas):
        if (1<last_meas[2]<range_value[0][0] and \
            range_value[0][1]<last_meas[-2]<range_value[0][2] and\
            216<last_meas[-1]<253):
            return False
        else: return True
        
    def blackOutRangeCheck(self, last_meas):
        if (self.v_lower_bound<last_meas[3]<self.v_upper_bound):
            return False
        else: return True

    def MQTTfaultyInterface(self, houseID, ID):
        client= ServiceBase("C:/Users/hp/Desktop/IOT/lab4_es4/faultyAppAndBlackout_control/serviceConfig_blackout_faulty.json")
        mqtt= MyMQTT(self.clientID,self.broker,1883,subNotifier=None)
        self.cur.execute("""SELECT switchesStates
                            FROM {}
                            WHERE deviceID = ? """.format(self.modules_and_switches),(ID,))
        switches = self.cur.fetchone()[0]
        topic="SmartModule/{}/dev/{}".format(houseID, ID)
        msg=  {
            "Faulty appliance":{  
            "Active": {
            "Module": 0, 
            "Switches": switches
        }}}
        
        client.MQTT.start()
        client.MQTT.Subscribe(topic)
        client.MQTT.Publish(topic, msg)
        client.MQTT.stop() 

    def MQTTblackoutInterface(self, houseID,):
        mqtt= MyMQTT(self.clientID,self.broker,1883,subNotifier=None)
        topic="SmartModule/{}".format(houseID)
        msg=  {
            "Blackout":{  
            "Active": {
            "Module": 0
        }}}
        
        mqtt.start()
        mqtt.Subscribe(topic)
        mqtt.Publish(topic, msg)
        mqtt.stop() 

    def controlAndDisconnect(self): #cont fino a 4?? 8 secondi
           self.cur.execute("""SELECT DISTINCT houseID
                                  FROM {}""".format(self.houses))
           houses = self.cur.fetchall()
           for house in houses:
               blackout_cont=0
               modules= self.houseInfo(house[0])
               for info in modules:
                   faulty_cont=0
                   value=self.getRange(info[0][0]) #info[i][0] = ID
                   last_measurement=self.lastValueCheck(info[0][0])#[id, time,power]
                   if self.blackOutRangeCheck(last_measurement):
                       blackout_cont+=1 
                   if blackout_cont > self.blackout_lim:
                       control.MQTTblackoutInterface(house[0])
                       break
                   if self.faultyRangeCheck(value, last_measurement):
                            prevRows=self.prevValuesCheck(info[0][0])
                            for prevValues in prevRows:
                                    if self.faultyRangeCheck(value, prevValues):
                                        faulty_cont+=1   
                            if faulty_cont>=4:
                                control.MQTTfaultyInterface(house[0], info[0][0])
         

if __name__ == "__main__":
    control= FaultyAppliancesDetection('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
    i=0
    while i<2: #poi ci andrà true
     control.controlAndDisconnect()
     i+=1
     time.sleep(2)