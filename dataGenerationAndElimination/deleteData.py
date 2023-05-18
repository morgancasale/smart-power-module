import sqlite3 as sq
import json
from datetime import datetime
import time
 
#statistics si possono tenere per un anno, per fare plot vecchi(?) o mese

#cambia da states1  a states (due volte)
#tengo un mese di dati?

class dev_conn_DB():
    
    def __init__(self, jsonfile):
        self.conn = sq.connect('C:/Users/hp/Desktop/IOT/lab4_es4/dbRC.sqlite')
        self.connHA = sq.connect('C:/Users/hp/Desktop/IOT/lab4_es4/testDB_Marika.db')
        self.cur = self.conn.cursor()
        self.curHA= self.connHA.cursor()
           
        self.dev_settings = 'DeviceSettings'
        self.database= 'states1'
        #analytics
        self.daily= 'dailyData'
        self.hourly= 'hourlyAvgData'
        self.monthly= 'monthlyData'
        self.yearly='yearlyData'
        self.less_than_yearly=[self.hourly, self.daily, self.monthly, self.yearly]

        self.day =86400 # un giorno di dati prendendone 1 ogni 2 secondi
        self.year= 31557600

    #controllo solo power tanto per current e voltage si ripeterebbe solo
    def oldestTimestamp(self, ID):
        partial=ID[1:]
        self.powerStateID= 'sensor.power_' + partial
        self.voltageStateID='sensor.voltage_' + partial
        self.currentStateID='sensor.curent_' + partial
        self.IDs=[self.powerStateID, self.voltageStateID, self.currentStateID]
        #return [(ID, max_timestamp, power)]
        self.curHA.execute("""
            SELECT MIN(last_updated_ts)
            FROM {}
            WHERE entity_id
            = ?""".format(self.database),(self.powerStateID,))
        result = self.curHA.fetchone()
        return result
    
    def oldestTimestampAnalytics(self, ID,table):
        self.curHA.execute("""
            SELECT MIN(timestamp)
            FROM {}
            WHERE deviceID
            = ?""".format(table),(ID,))
        result = self.curHA.fetchone()
      
        return result
       

    def deleteAnalyticsData(self):
        self.cur.execute("""SELECT deviceID 
                            FROM {}""".format(self.dev_settings))
        modules = self.cur.fetchall()
        for module in modules:
             for table in self.less_than_yearly: 
                oldest_ts=self.oldestTimestampAnalytics(module[0],table)
                print(oldest_ts[0])
                print(type(oldest_ts[0]))
                if (oldest_ts[0] is not None and (time.time()- oldest_ts[0]) > self.year): 
                    self.curHA.execute("""
                                    DELETE
                                    FROM {}
                                    WHERE timestamp = ? 
                                    AND deviceID = ?
                                    """.format(table),(oldest_ts[0],module[0]))
                    self.connHA.commit()
                    print('updated')



    def deleteOldestEntryDB(self):
        self.cur.execute("""SELECT deviceID 
                            FROM {}""".format(self.dev_settings))
        modules = self.cur.fetchall()
       
        for module in modules:
            oldest_ts=self.oldestTimestamp(module[0])

        if (oldest_ts != None and (time.time()- oldest_ts[0]) > self.day): 
            for ID in self.IDs: #because we have hre type of measurements
                self.curHA.execute("""
                                DELETE
                                FROM states1 
                                WHERE last_updated_ts = ? 
                                AND entity_id = ?
                                """, (oldest_ts[0],ID))
                self.connHA.commit()
                print('updated')
       
        #self.cur.close()
        #self.curHA.close()
        

        

if __name__ == "__main__":
    #change path
    #
    modifyDB = dev_conn_DB('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/device.json')
    #apri qui conn
    modifyDB.deleteAnalyticsData()
    modifyDB.deleteOldestEntryDB()
    











    
    
    
    