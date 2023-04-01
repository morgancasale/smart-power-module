import sqlite3
class StandByPowerDetection():

    def __init__(self,database):
        self.conn = sqlite3.connect('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
        self.cur = self.conn.cursor()
        self.database= 'PROVA_database'
        self.modules_and_switches='PROVA_m_s'
        self.ranges='PROVA_device_ranges'
        self.devices_db= 'PROVA_devices'

    
    def prevValuesCheck(self, moduleID):
        # Retrieve the 10 largest values of the timestamp column for the given moduleID
        self.cur.execute("""
            SELECT moduleID, timestamp, power FROM (
                SELECT moduleID, timestamp, power, ROW_NUMBER() 
                OVER (ORDER BY timestamp DESC) AS row_num
                FROM {}
                WHERE moduleID = ?
            )
            WHERE row_num <= 10
        """.format(self.database), (moduleID,))
        # Fetch the results
        results = self.cur.fetchall()
        #for result in results:
        #    print(f"ID: {result[0]}, timestamp: {result[1]}")
        return results
       
    def lastValueCheck(self, ID):
        #return [(ID, max_timestamp, power)]
        #  retrieve the maximum value of timestamp column for each ID
        self.cur.execute("""
            SELECT moduleID, MAX(timestamp), power
            FROM {}
            WHERE moduleID
            LIKE {}""".format(self.database,ID))
        results = self.cur.fetchone()
        
        return results

    def standByPowerCheck(self):
        #cambia valore (2 o 3 minuti)
        lv= self.lastValueCheck() #to be finished
    
        
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
           self.cur.execute("""SELECT standByPowerMax
                             FROM {} 
                             WHERE type
                             = ?""".format(self.ranges), (device_type))
           dev_range = self.cur.fetchone()[0]
           if dev_range is not None:
               return dev_range
           else:
               return None
            
    def modifyModuleState(self, ID):
        # Update the state value for the given ID
        self.cur.execute("""
            UPDATE {} 
            SET module_state={}
            WHERE moduleID={}
        """.format(self.modules_and_switches, 0, ID))
        self.conn.commit()
    #stacco tutto il modulo tanto c'è un solo elettrodomestico

    def controlAndDisconnect(self):
       # i=0#poi leva quad fai la request ogni due secondi
        #while (i < 10):#leva quando sistemi parte request
         #   i+=1#poi leva
            modInfo = self.moduleInfo()
            for info in modInfo:
                cont=0
                if (info[1]==1 and sum(info[2:])==1):
                    value=self.getRange(info[0]) #info[i][0] = ID
                    last_measurement=self.lastValueCheck(info[0])#[id, time,power]
                    if (last_measurement[2]>=1 or last_measurement[2]<=value):
                            prevRows=self.prevValuesCheck(info[0])
                            for prevValues in prevRows:
                                    if (prevValues[2]>=1 or prevValues[2]<=value):
                                        cont+=1   
                            
                            if cont>=4:
                                self.modifyModuleState(info[0])

if __name__ == "__main__":
    control= StandByPowerDetection('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
    control.controlAndDisconnect()
            
