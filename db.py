import sqlite3 as sq
import json
from datetime import datetime
import time
 

class dev_conn_DB():
    
    def __init__(self, jsonfile):
        with sq.connect("C:/Users/hp/Desktop/IOT/lab4_es4/data_m.sqlite") as self.conn:
        #self.conn = sq.connect("C:/Users/hp/Desktop/IOT/lab4_es4/data_m.sqlite")
            self.cursor = self.conn.cursor()
            self.module_and_switches = 'Devices'
            self.database= 'data'
            self.max_rows =382466 # un mese di dati prendendone 1 ogni 6 secondi

        
        conf = json.load(open(jsonfile))
        switch = str(conf["Data"]["Active"]["Switches"])
        my_list = json.loads(switch)
        self.switches = str([str(i) for i in my_list])
        self.module = conf["Data"]["Active"]["Module"]
        self.passive = conf["Data"]["Passive"]
        self.moduleID = conf["deviceID"]
        print(self.moduleID)
        timedate=conf["timestamp"]
        self.timestamp = int(time.mktime(time.strptime(timedate, "%Y-%m-%dT%H:%M:%SZ")))


    def addNewEntryDB(self):
        values= (self.moduleID, self.passive['Power'], self.passive['Voltage'],\
                 self.passive['Current'], self.timestamp)
        self.cursor.execute("""INSERT INTO {} 
                            (deviceID, power, voltage, current, timestamp) 
                         VALUES (?,?,?,?,?)""".format(self.database), values)
        self.conn.commit()
        print('updated')
        
        
        
    def deleteOldestEntry(self):
        self.cursor.execute("""SELECT COUNT(*)
                            FROM {} 
                            WHERE deviceID=?""".format(self.database), (self.moduleID,))
        result = self.cursor.fetchone()[0]
        if result > self.max_rows: 
            self.cursor.execute("""
                            DELETE 
                            FROM data_prova
                            WHERE timestamp = (
                            SELECT MIN(timestamp)
                            FROM data_prova
                            WHERE deviceID=?
                            )
                            AND deviceID=?
                        """, (self.moduleID, self.moduleID))
            self.conn.commit()
            print('updated')
       
        self.cursor.close()
        
    
    def updateDevices(self):
        self.cursor.execute("""
            UPDATE {} 
            SET lastUpdate=?, moduleState=?,switchesStates=?
            WHERE deviceID=?
        """.format(self.module_and_switches), (self.timestamp, self.module, self.switches, self.moduleID))
        self.conn.commit()
        print("Record updated")
        

if __name__ == "__main__":
    #change path
    #
    modifyDB = dev_conn_DB('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/device.json')
    modifyDB.updateDevices()
    modifyDB.addNewEntryDB()
    modifyDB.deleteOldestEntry()
    











    
    
    
    