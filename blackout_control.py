import sqlite3

class BlackoutDetection():

    def __init__(self,database):
        self.conn = sqlite3.connect('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
        self.cur = self.conn.cursor()
        self.houses='PROVA_houseConn'
        self.database= 'PROVA_database'
        self.modules_and_switches='PROVA_m_s'
        #self.ranges='PROVA_device_ranges'
        #self.devices_db= 'PROVA_devices'
        self.lower_voltage_bound=216
        self.upper_voltage_bound=253

    def houseInfo(self,house_ID):
        #this method retrieves the modules belonging to each home that are on+
        #and have one device cnnected to them
        to_consider=[]
        self.cur.execute("""SELECT moduleID
                         FROM {} 
                         WHERE houseID = ?""".format(self.houses),(house_ID,))
        house_modules= self.cur.fetchall()
        for house_module in house_modules :
            self.cur.execute("""SELECT *
                             FROM {}
                             WHERE moduleID = ? """.format(self.modules_and_switches),(house_module))
            result = self.cur.fetchall()
            if ( result[0][1] == 1 and sum(result[0][2:])==1):
                to_consider.append(result[0][0])
        if (to_consider) is not None:
            return (to_consider)
        else: return None


    def lastValueCheck(self, ID):
        #return [(ID, max_timestamp, power)]
        #  retrieve the maximum value of timestamp column for each ID
        self.cur.execute("""
            SELECT moduleID, MAX(timestamp), voltage
            FROM {}
            WHERE moduleID
            LIKE {}""".format(self.database,ID))
        results = self.cur.fetchone()
        return results
        
    def ModifyModulesState(self):
        # Update the state value for the given ID
        self.cur.execute("""
            UPDATE {} 
            SET module_state=0
        """.format(self.modules_and_switches))
        self.conn.commit()
        
    def ModulesCheckAndTurnOff(self):
        self.cur.execute("""SELECT DISTINCT houseID
                            FROM {}""".format(self.houses))
        houses = self.cur.fetchall()
        for house in houses:
            cont=0
            modules= control.houseInfo(house[0])#se non funziona e questo
            for module in modules:
                last_val=control.lastValueCheck(module)
                if (last_val[2] < control.lower_voltage_bound or last_val[2]>control.upper_voltage_bound):
                    cont+=1
            limit_occurences=int(0.5*len(modules)) #20% cambiaaaaaaaa
            if cont >= limit_occurences :
                control.ModifyModulesState()
        
    
#IMPP se un valore è sballato e ne contorllo solo uno stacco in faulty
#ci sta controllare il 20% degli elettrodomestici?
if __name__ == "__main__":
    control= BlackoutDetection('C:/Users/hp/Desktop/IOT/lab4_es4/data.db')
    control.ModulesCheckAndTurnOff()