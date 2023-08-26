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
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%'"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
                case "gethourlydata":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    test=params
                    query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%_tothourly%' "
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
                case "getdailydata":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    test=params
                    query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%_totdaily%'"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
                case "getmonthlydata":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    test=params
                    query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%_totmonthly%'"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getyearlydata":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    test=params
                    query="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                        FROM states2\
                        WHERE entity_id LIKE 'sensor.%_totyearly%'"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
                case "gethourlydata_byhouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                            FROM states2\
                            WHERE entity_id LIKE 'sensor.%_tothourly%'"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                            FROM HouseDev_conn\
                            WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()

                    combined_results = []
                    # Iterate through the rows from the first database
                    for row1 in rows1:
                        entity_id= row1[0]
                        state= row1[1]
                        timestamp=row1[2]
                        entity_id_parts = entity_id.split("_")
                        if len(entity_id_parts) >= 2:
                            if entity_id_parts[-2] == 'tothourly':
                                deviceID = 'D'+ entity_id_parts[-1]
                            elif entity_id_parts[-1] == 'tothourly':
                                deviceID = 'D1'
                            else:
                                deviceID = None
                        else:
                            deviceID = None
                        # Handle the case where entity_id doesn't match the expected format
                        # Check if the deviceID is in the list of deviceIDs for house H1
                        for row2 in rows2:
                            if row2[1] == deviceID:
                                combined_results.append((entity_id, state,timestamp))
                    # Convert the combined results to a JSON string
                    json_string = json.dumps(combined_results)
                    return json_string
                
                case "getdailydata_byhouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                            FROM states2\
                            WHERE entity_id LIKE 'sensor.%_totdaily%'"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                            FROM HouseDev_conn\
                            WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()

                    combined_results = []
                    # Iterate through the rows from the first database
                    for row1 in rows1:
                        entity_id= row1[0]
                        state= row1[1]
                        timestamp=row1[2]
                        entity_id_parts = entity_id.split("_")
                        if len(entity_id_parts) >= 2:
                            if entity_id_parts[-2] == 'totdaily':
                                deviceID = 'D'+ entity_id_parts[-1]
                            elif entity_id_parts[-1] == 'totdaily':
                                deviceID = 'D1'
                            else:
                                deviceID = None
                        else:
                            deviceID = None
                        # Handle the case where entity_id doesn't match the expected format
                        # Check if the deviceID is in the list of deviceIDs for house H1
                        for row2 in rows2:
                            if row2[1] == deviceID:
                                combined_results.append((entity_id, state,timestamp))
                    # Convert the combined results to a JSON string
                    json_string = json.dumps(combined_results)
                    return json_string
                
                case "getmonthlydata_byhouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                            FROM states2\
                            WHERE entity_id LIKE 'sensor.%_totmonthly%'"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                            FROM HouseDev_conn\
                            WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()

                    combined_results = []
                    # Iterate through the rows from the first database
                    for row1 in rows1:
                        entity_id= row1[0]
                        state= row1[1]
                        timestamp=row1[2]
                        entity_id_parts = entity_id.split("_")
                        if len(entity_id_parts) >= 2:
                            if entity_id_parts[-2] == 'totmonthly':
                                deviceID = 'D'+ entity_id_parts[-1]
                            elif entity_id_parts[-1] == 'totmonthly':
                                deviceID = 'D1'
                            else:
                                deviceID = None
                        else:
                            deviceID = None
                        # Handle the case where entity_id doesn't match the expected format
                        # Check if the deviceID is in the list of deviceIDs for house H1
                        for row2 in rows2:
                            if row2[1] == deviceID:
                                combined_results.append((entity_id, state,timestamp))
                    # Convert the combined results to a JSON string
                    json_string = json.dumps(combined_results)
                    return json_string
                
                case "getyearlydata_byhouseID":
                    # Connect to the first database
                    conn1 = sqlite3.connect(DBPath)
                    curs1 = conn1.cursor()
                    # Connect to the second database
                    conn2 = sqlite3.connect(DBPath2)
                    curs2 = conn2.cursor()
                    # Execute the query
                    houseID=params
                    # Execute query on the first database
                    query1="SELECT entity_id, state, strftime('%Y-%m-%d %H:%M:%S', datetime(last_updated_ts, 'unixepoch')) as timestamp\
                            FROM states2\
                            WHERE entity_id LIKE 'sensor.%_totyearly%'"
                    curs1.execute(query1)
                    rows1 = curs1.fetchall()

                    query2="SELECT houseID, deviceID\
                            FROM HouseDev_conn\
                            WHERE houseID=?"
                    curs2.execute(query2,(houseID,))
                    rows2 = curs2.fetchall()

                    combined_results = []
                    # Iterate through the rows from the first database
                    for row1 in rows1:
                        entity_id= row1[0]
                        state= row1[1]
                        timestamp=row1[2]
                        entity_id_parts = entity_id.split("_")
                        if len(entity_id_parts) >= 2:
                            if entity_id_parts[-2] == 'totyearly':
                                deviceID = 'D'+ entity_id_parts[-1]
                            elif entity_id_parts[-1] == 'totyearly':
                                deviceID = 'D1'
                            else:
                                deviceID = None
                        else:
                            deviceID = None
                        # Handle the case where entity_id doesn't match the expected format
                        # Check if the deviceID is in the list of deviceIDs for house H1
                        for row2 in rows2:
                            if row2[1] == deviceID:
                                combined_results.append((entity_id, state,timestamp))
                    # Convert the combined results to a JSON string
                    json_string = json.dumps(combined_results)
                    return json_string
                
                case "gethouses_list":
                    conn = sqlite3.connect(DBPath2)
                    curs = conn.cursor()
                    test=params
                    query="SELECT houseID\
                            FROM Houses"
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string


        except web_exception as e:
            return ("An error occurred while handling the GET request: " + e.message)

    def handlePutRequest(self, comando, params):
        try:
            match comando:
                case "putData":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    bodydata=json.loads(params)
                    entity_id=bodydata["entity_id"]
                    state=bodydata["state"]
                    last_updated_ts=int((datetime.datetime.strptime(bodydata["timestamp"], "%Y-%m-%d %H:%M:%S")).timestamp())  
                    query="INSERT INTO states2 (entity_id, state,last_updated_ts) VALUES (?, ?, ?);"
                    curs.execute(query,(entity_id,state,last_updated_ts))
                    cn.commit()
                    # Confirm successful updating of person information.
                    print("Information updated successfully.")   


        except web_exception as e:
            return ("An error occurred while handling the PUT request: " + e.message)           
    

class web_exception(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)