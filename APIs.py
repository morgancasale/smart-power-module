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
                case "getAllbyID":
                    cn=self.connessione.create_connection()
                    id=params
                    curs=cn.cursor()
                    query="SELECT strftime('%Y-%m-%d %H', datetime(timestamp, 'unixepoch')) AS date,\"power(w)\",\"current(A)\",\"voltage(V)\"\
                          FROM database where ID=?"
                    curs.execute(query,(id,))
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                    
                    
                #Ad ogni casa è associata una table "database_idcasa". Grazie a questa funzione posso recuperare tutti i dati relativi alla casa di nostro interesse.    
                case "getAlldbbyID":
                    cn=self.connessione.create_connection()
                    idHouse=params
                    table="database"+idHouse
                    curs=cn.cursor()
                    query="SELECT ID, strftime('%Y-%m-%d %H:%M:%S', datetime(timestamp, 'unixepoch')) AS date,\"power(w)\",\"current(A)\",\"voltage(V)\"\
                          FROM "+table
                    curs.execute(query)
                    rows = curs.fetchall()
                    json_string = json.dumps(rows)
                    return json_string
                
        except web_exception as e:
            return ("An error occurred while handling the GET request: " + e.message)
    

class web_exception(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)