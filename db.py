import sqlite3 as sq
import json
from datetime import datetime
import time
 

class dev_conn_DB():
    
    def __init__(self, jsonfile):
        self.conn = sq.connect("C:/Users/hp/Desktop/IOT/lab4_es4/data_m.sqlite")
        self.cursor = self.conn.cursor()
        self.module_and_switches = 'Devices'
        self.database= 'data'

        
        conf = json.load(open(jsonfile))
        switch = str(conf["Data"]["Active"]["Switches"])
        my_list = json.loads(switch)
        self.switches = str([str(i) for i in my_list])
        self.module = conf["Data"]["Active"]["Module"]
        self.passive = conf["Data"]["Passive"]
        self.moduleID = conf["deviceID"]
        timedate=conf["timestamp"]
        #timedate= "2019-03-01T12:00:00Z"
        self.timestamp = int(time.mktime(time.strptime(timedate, "%Y-%m-%dT%H:%M:%SZ")))
   
        
        #self.timestamp = date_object.strftime("%Y-%m-%d %H:%M:%S")

    def addEntryDB(self):
        values= (modifyDB.moduleID, modifyDB.passive['Power'], modifyDB.passive['Voltage'],\
                 modifyDB.passive['Current'], modifyDB.timestamp)
        modifyDB.cursor.execute("""INSERT INTO {} 
                            (deviceID, power, voltage, current, timestamp) 
                            VALUES (?,?,?,?,?)""".format(modifyDB.database), values)
        modifyDB.conn.commit()
        print('updated')
        modifyDB.cursor.close()
        
        
    def updateDevices(self):
        self.cursor.execute("""
            UPDATE {} 
            SET lastUpdate=?, moduleState=?,switchesStates=?
            WHERE deviceID=?
        """.format(self.module_and_switches), (self.timestamp, self.module, self.switches, self.moduleID))
        self.conn.commit()
        print("Record updated")

if __name__ == "__main__":
    modifyDB = dev_conn_DB('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/device.json')
    modifyDB.updateDevices()
    modifyDB.addEntryDB()
    modifyDB.cursor.close()
    














    
    
    
    