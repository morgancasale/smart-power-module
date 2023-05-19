import json
import pandas as pd
import sqlite3 
import connect_db
import datetime

DBPath = "Data_DB/testDB.db"
DBPath2 = "Data_DB/db.sqlite"

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
                    query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                          FROM states1\
                          WHERE entity_id NOT LIKE 'switch%'"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
                case "getAllbyDay":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query="SELECT deviceID, SUBSTRING(strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch')),1,10) as day, SUM(power) as total_power, SUM(current) as total_current, SUM(voltage) as total_voltage\
                           FROM hourlyAvgData\
                           GROUP BY deviceID,day"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getAllbyMonth":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query="SELECT deviceID, SUBSTRING((strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch')),1,7) as month, SUM(power) as monthly_power, SUM(current) as monthly_current, SUM(voltage) as total_monthly_voltage\
                          FROM dailyData\
                          GROUP BY deviceID,month"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getAllbyYear":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query="SELECT deviceID, SUBSTRING((strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch'))),1,4) as year, SUM(power) as monthly_power, SUM(current) as monthly_current, SUM(voltage) as total_yearly_voltage\
                          FROM monthlyData\
                          GROUP BY deviceID,year"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string

                case "getHourlyDatabyHouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT *\
                            FROM hourlyAvgData"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                          FROM HouseDev_conn\
                          WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()

                    combined_results = []
                    for row1 in rows1:
                        deviceID = row1[0]
                        voltage= row1[1]
                        current=row1[2]
                        power = row1[3]
                        timestamp= row1[4]
                        for row2 in rows2:
                             if row2[1] == deviceID:
                                houseID = row2[0]
                                combined_results.append((houseID, deviceID,timestamp, voltage, current, power))
                    
                    json_string = json.dumps(combined_results)
                    return json_string  

                case "getDailyDatabyHouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT *\
                            FROM dailyData"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                          FROM HouseDev_conn\
                          WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()
                    
                    combined_results = []
                    for row1 in rows1:
                        deviceID = row1[0]
                        voltage= row1[1]
                        current=row1[2]
                        power = row1[3]
                        timestamp= row1[4]
                        for row2 in rows2:
                             if row2[1] == deviceID:
                                houseID = row2[0]
                                combined_results.append((houseID, deviceID,timestamp, voltage, current, power))
                    
                    json_string = json.dumps(combined_results)
                    return json_string      
                
                case "getMonthlyDatabyHouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT *\
                            FROM monthlyData"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                          FROM HouseDev_conn\
                          WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()
                    combined_results = []
                    for row1 in rows1:
                        deviceID = row1[0]
                        voltage= row1[1]
                        current=row1[2]
                        power = row1[3]
                        timestamp= row1[4]
                        for row2 in rows2:
                             if row2[1] == deviceID:
                                houseID = row2[0]
                                combined_results.append((houseID, deviceID,timestamp, voltage, current, power))
                    
                    json_string = json.dumps(combined_results)
                    return json_string 
                
                case "getYearlyDatabyHouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT *\
                            FROM yearlyData"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                          FROM HouseDev_conn\
                          WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()
                    combined_results = []
                    for row1 in rows1:
                        deviceID = row1[0]
                        voltage= row1[1]
                        current=row1[2]
                        power = row1[3]
                        timestamp= row1[4]
                        for row2 in rows2:
                             if row2[1] == deviceID:
                                houseID = row2[0]
                                combined_results.append((houseID, deviceID,timestamp, voltage, current, power))
                    
                    json_string = json.dumps(combined_results)
                    return json_string     
       
        except web_exception as e:
            return ("An error occurred while handling the GET request: " + e.message)

    def handlePostRequest(self, comando):
        try:
            match comando:
                case "createHourlyTable":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query = "CREATE TABLE hourlyAvgData (deviceID TEXT,Voltage FLOAT, Current FLOAT, Power FLOAT,timestamp FLOAT);"
                    curs.execute(query)
                    cn.commit()                  

                case "createDailyTable":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query = "CREATE TABLE dailyData (deviceID TEXT,Voltage FLOAT, Current FLOAT, Power FLOAT,timestamp FLOAT);"
                    curs.execute(query)
                    cn.commit()

                case "createMonthlyTable":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query = "CREATE TABLE monthlyData (deviceID TEXT,Voltage FLOAT, Current FLOAT, Power FLOAT,timestamp FLOAT);"
                    curs.execute(query)
                    cn.commit()

                case "createYearlyTable":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    query = "CREATE TABLE yearlyData (deviceID TEXT,Voltage FLOAT, Current FLOAT, Power FLOAT,timestamp FLOAT);"
                    curs.execute(query)
                    cn.commit()

        except web_exception as e:
            return ("An error occurred while handling the POST request: " + e.message)    
                
  
    def handlePutRequest(self, comando, params):
        try:
            match comando:
                case "putHourlyData":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=int((datetime.datetime.strptime(bodydata["timestamp"], "%Y-%m-%d %H:%M:%S")).timestamp())  
                    query="INSERT INTO hourlyAvgData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Information updated successfully.")

                case "putDailyData":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=int((datetime.datetime.strptime(bodydata["timestamp"], "%Y-%m-%d %H:%M:%S")).timestamp())  
                    query="INSERT INTO dailyData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Information updated successfully.")  


                case "putMonthlyData":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=int((datetime.datetime.strptime(bodydata["timestamp"], "%Y-%m-%d %H:%M:%S")).timestamp())  
                    query="INSERT INTO monthlyData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Information updated successfully.")

                case "putYearlyData":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    deviceID=bodydata["deviceID"]
                    Voltage=bodydata["Voltage"]
                    Current=bodydata["Current"]
                    Power=bodydata["Power"]
                    timestamp=int((datetime.datetime.strptime(bodydata["timestamp"], "%Y-%m-%d %H:%M:%S")).timestamp())                  
                    query="INSERT INTO yearlyData (deviceID, Voltage, Current, Power,timestamp) VALUES (?, ?, ?,?, ?);"
                    curs.execute(query,(deviceID,Voltage,Current,Power,timestamp))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Information updated successfully.")

                #case _:
                 #   raise web_exception(400, "Unexpected invalid command")
                    
        except web_exception as e:
            return ("An error occurred while handling the PUTrequest: " + e.message)          


class web_exception(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)