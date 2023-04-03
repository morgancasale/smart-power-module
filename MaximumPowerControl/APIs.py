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
                case "getlastPower":
                    cn=self.connessione.create_connection()
                    id=params
                    curs=cn.cursor()
                    query="SELECT ID, max(strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch'))) as date,power\
                          FROM database,HouseDev_conn\
                          WHERE ID==moduleID and houseID=?\
                          GROUP BY ID"
                    curs.execute(query,(id,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
                case "getMaxPowerHouse":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    id=params
                    query="SELECT houseID,PotenzaContatore\
                          FROM Houses\
                          WHERE houseID=?"
                    curs.execute(query,(id,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                case "getLastUpdate":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    id=params
                    query="SELECT Devices.moduleID, max((lastUpdate)) as date,online\
                          FROM Devices,HouseDev_conn\
                          WHERE Devices.moduleID=HouseDev_conn.moduleID and houseID=? and online='1'"
                    curs.execute(query,(id,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string    
            
                
        except web_exception as e:
            return ("An error occurred while handling the GET request: " + e.message)
            
    def handlePatchRequest(self, comando, params):
        try:
            match comando:
                case "updateModule":
                    cn=self.connessione.create_connection()
                    curs=cn.cursor()
                    id=params
                    query="UPDATE PROVA_m_s\
                           SET module_state=0\
                           WHERE moduleID=?"
                    curs.execute(query,(int(id),))
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
    