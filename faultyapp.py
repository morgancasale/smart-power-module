import sqlite3

class FaultyAppliancesDetection():

    def __init__(self,database):
        self.conn = sqlite3.connect('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
        self.cur = self.conn.cursor()
        self.database= 'PROVA_database'
        self.modules_and_switches='PROVA_m_s'
        self.ranges='PROVA_device_ranges'
        self.devices_db= 'PROVA_devices'
        self.v_upper_bound=253
        self.v_lower_bound=216
    
    def prevValuesCheck(self, moduleID):
        # Retrieve the 10 largest values of the timestamp column for the given moduleID
        self.cur.execute("""
            SELECT moduleID, power, voltage FROM (
                SELECT moduleID, power, voltage, ROW_NUMBER() 
                OVER (ORDER BY timestamp DESC) AS row_num
                FROM {}
                WHERE moduleID = ?
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
            SELECT moduleID, MAX(timestamp), power,  voltage
            FROM {}
            WHERE moduleID
            LIKE {}""".format(self.database,ID))
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
        
    def getRange(self, ID):   
           self.cur.execute("""SELECT type 
                            FROM {} 
                            WHERE moduloID
                            = ?""".format(self.devices_db), (ID,))
           device_type = self.cur.fetchone()[0]
           self.cur.execute("""SELECT standByPowerMax, functioningRangeMin, functioningRangeMax
                             FROM {} 
                             WHERE type
                             = ?""".format(self.ranges), (device_type,))
           dev_range = self.cur.fetchall()
           if dev_range is not None:
               return dev_range
           else:
               return None
    
    def rangeCheck(self, range_value, last_meas):
        if (1<last_meas[-2]<range_value[0][0] and \
            range_value[0][1]<last_meas[-2]<range_value[0][2] and\
            216<last_meas[-1]<253):
            return False
        else: return True
        
        
            
    def modifyModuleState(self, ID):
        # Update the state value for the given ID
        self.cur.execute("""
            UPDATE {} 
            SET module_state={}
            WHERE moduleID={}
        """.format(self.modules_and_switches, 0, ID))
        self.conn.commit()
    #stacco tutto il modulo tanto c'è un solo elettrodomestico

    def controlAndDisconnect(self): #cont fino a 4?? 8 secondi
            modInfo = self.moduleInfo()
            for info in modInfo:
                cont=0
                if (info[1]==1 and sum(info[2:])==1):
                    value=self.getRange(info[0]) #info[i][0] = ID
                    last_measurement=self.lastValueCheck(info[0])#[id, time,power]
                    if self.rangeCheck(value, last_measurement):
                            prevRows=self.prevValuesCheck(info[0])
                            for prevValues in prevRows:
                                    if self.rangeCheck(value, prevValues):
                                        cont+=1   
                            if cont>=4:
                                self.modifyModuleState(info[0])

if __name__ == "__main__":
    control= FaultyAppliancesDetection('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
    control.controlAndDisconnect()
   
    
            