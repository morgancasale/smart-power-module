import json
import pandas as pd
import sqlite3 
import connect_db
DBPath = "Data_DB/data.db"
class api_server():
    def __init__(self,connessione):
        self.connessione=connessione

    def handleRequestGET(self,comando,params):
        try:
            match comando:               
                case "getAlldb":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    test=params
                    query="SELECT deviceID, strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch')) AS date,power,current,voltage\
                          FROM database"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getAllbyDay":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query="SELECT deviceID, SUBSTRING(timestamp,1,10) as day, SUM(power) as total_power, SUM(current) as total_current, AVG(voltage) as avg_voltage\
                           FROM hourlyAvgData\
                           GROUP BY deviceID,day"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getAllbyMonth":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query="SELECT deviceID, SUBSTRING(timestamp,1,7) as month, SUM(power) as monthly_power, SUM(current) as monthly_current, AVG(voltage) as avg_monthly_voltage\
                          FROM dailyAvgData\
                          GROUP BY deviceID,month"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getAllbyYear":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query="SELECT deviceID, SUBSTRING(timestamp,1,4) as year, SUM(power) as monthly_power, SUM(current) as monthly_current, AVG(voltage) as avg_monthly_voltage\
                          FROM monthlyAvgData\
                          GROUP BY deviceID,year"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string

                case "getHourlyDatabyHouseID":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    id=params
                    query="SELECT hourlyAvgData.deviceID, timestamp AS date,power,voltage,current\
                          FROM hourlyAvgData,HouseDev_conn\
                          WHERE hourlyAvgData.deviceID==HouseDev_conn.deviceID and houseID=?"
                    curs.execute(query,(id,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string  

                case "getDailyDatabyHouseID":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    houseID=params
                    query="SELECT dailyAvgData.deviceID, timestamp AS date,power,voltage,current\
                          FROM dailyAvgData,HouseDev_conn\
                          WHERE dailyAvgData.deviceID==HouseDev_conn.deviceID and houseID=?"
                    curs.execute(query,(houseID,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string    
                
                case "getMonthlyDatabyHouseID":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    houseID=params
                    query="SELECT monthlyAvgData.deviceID, timestamp AS date,power,voltage,current\
                          FROM monthlyAvgData,HouseDev_conn\
                          WHERE monthlyAvgData.deviceID==HouseDev_conn.deviceID and houseID=?"
                    curs.execute(query,(houseID,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string    
                
                case "getYearlyDatabyHouseID":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    houseID=params
                    query="SELECT yearlyAvgData.deviceID, timestamp AS date,power,voltage,current\
                          FROM yearlyAvgData,HouseDev_conn\
                          WHERE yearlyAvgData.deviceID==HouseDev_conn.deviceID and houseID=?"
                    curs.execute(query,(houseID,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string    


                    
                
                    
        except web_exception as e:
            return ("An error occurred while handling the GET request: " + e.message)
        
  
    def handlePutRequest(self, comando, params):
        try:
            match comando:
                case "putTest":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=bodydata["timestamp"]
                    query="INSERT INTO hourlyAvgData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Person information updated successfully.")

                case "putTest2":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=bodydata["timestamp"]
                    query="INSERT INTO dailyAvgData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Person information updated successfully.")  


                case "putTest3":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=bodydata["timestamp"]
                    query="INSERT INTO monthlyAvgData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Person information updated successfully.")

                case "putTest4":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=bodydata["timestamp"]
                    query="INSERT INTO yearlyAvgData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Person information updated successfully.")

                    
                #case _:
                 #   raise web_exception(400, "Unexpected invalid command")
                    
        except web_exception as e:
            return ("An error occurred while handling the PATCH request: " + e.message)          
                    
    

class web_exception(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)