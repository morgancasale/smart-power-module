import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

import pandas as pd
import sqlite3 as sq
import json
from datetime import datetime
import re

from cherrypy import HTTPError

broker = "broker.hivemq.com"

from microserviceBase.serviceBase import *

def check_presence_inDB(DBPath, table, keyName, keyValue, caseSensitive = True):
    try:
        if(not isinstance(keyName, list)) : keyName = [keyName]
        if(not isinstance(keyValue, list)) : keyValue = [keyValue]

        keyValue = [str(value) for value in keyValue]

        keyName = "(" + ", ".join(keyName) + ")"
        keyValue = "(\"" + "\", \"".join(keyValue) + "\")"

        query = "SELECT COUNT(*)>0 as result FROM " + table + " WHERE " + keyName + " = " + keyValue
        if(not caseSensitive):
            query += " COLLATE NOCASE"
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"]) #True if the keyValue is present in the DB
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while extracting data from DB:\u0085\u0009" + str(e))
    

def check_presence_ofColumnInDB(DBPath, table, columnName):
    try:
        query = "SELECT COUNT(*)>0 AS result FROM pragma_table_info(\"" + table + "\") WHERE name=\"" + columnName + "\""
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"])
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while extracting data from DB:\u0085\u0009" + str(e))

def check_presence_ofTableInDB(DBPath, table):
    try:
        query = "SELECT COUNT(*)>0 AS result FROM sqlite_master WHERE (type, name) = (\"table\", \"" + table + "\")"
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"])
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while extracting data from DB:\u0085\u0009" + str(e))

def check_presence_inConnectionTables(DBPath, tables, keyName, keyValue):
    try:
        result = True
        for table in tables:
            if(check_presence_ofColumnInDB(DBPath, table, keyName)):
                result &= check_presence_inDB(DBPath, table, keyName, keyValue)
        
        return result
    except HTTPError as e:
        raise HTTPError(status=e.status, message="An error occured while checking presence in DB:\u0085\u0009" + e._message)
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while checking presence in DB:\u0085\u0009" + str(e))

def save_entry2DB(DBPath, table, entryData):
    try:
        conn = sq.connect(DBPath)
        query = "INSERT INTO " + table 
        query += "(\"" + "\", \"".join(entryData.keys()) + "\")"
        query += " VALUES "
        values = []
        for value in entryData.values():
            if(isinstance(value, list)):                
                if(len(value) > 0 and isinstance(value[0], int)):
                    value = [str(v) for v in value]
                
                value = json.dumps(value).replace("\"", "\'")
            if(isinstance(value, dict)):
                value = json.dumps(value).replace("\"", "\'")            
            if(value == None):
                value = "NULL"
            if(isinstance(value, bool)):
                value = str(int(value))
            if(isinstance(value, (int, float))):
                value = str(value)

            values.append(value)
        query += "(\"" + "\", \"".join(values) + "\")"

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while saving data to DB:\u0085\u0009" + str(e))

def update_entry_inDB(DBPath, table, primaryKeyNames, entryData):
    r"""
    - table: the table to update
    - primaryKeyNames: the name of the keys to find the entry to update
    - entryData: the values of the primaryKey and the data to update ({keyName : keyValue})
    """
    if(not isinstance(primaryKeyNames, list)) : primaryKeyNames = [primaryKeyNames]
    try:
        conn = sq.connect(DBPath)
        query = "UPDATE " + table + " SET "

        keys = []
        edatas = []
        for key, value in entryData.items():
            if key not in primaryKeyNames:
                keys.append(key)

                if(isinstance(value, list)):
                    if(len(value) > 0 and isinstance(value[0], int)):
                        value = [str(v) for v in value]
                    value = json.dumps(value).replace("\"", "\'")
                if(isinstance(value, dict)):
                    value = json.dumps(value).replace("\"", "\'")            
                if(value == None):
                    value = "NULL"
                if(isinstance(value, bool)):
                    value = str(int(value))
                if(isinstance(value, (int, float))):
                    value = str(value)

                edatas.append(value)

        keys = "(\"" + ("\", \"").join(keys)+"\")"
        edatas = "(\"" + ("\", \"").join(edatas) + "\")"

        query += keys + " = "
        query += edatas

        primaryKeyNamesQuery = "(\"" + ("\", \"").join(primaryKeyNames)+"\")"
        query += " WHERE " + primaryKeyNamesQuery + " = "

        primaryKeyValues = []
        for key in primaryKeyNames:
            primaryKeyValues.append(entryData[key])
        values = "(\"" + ("\", \"").join(primaryKeyValues) + "\")"
        query += values

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message=str(e))

def delete_entry_fromDB(DBPath, table, keyName, keyValue):
    try:
        if(not isinstance(keyName, list)) : keyName = [keyName]
        if(not isinstance(keyValue, list)) : keyValue = [keyValue]

        keyValue = [str(value) for value in keyValue]

        conn = sq.connect(DBPath)
        conn.execute("PRAGMA foreign_keys = ON")

        keyName = "(" + ", ".join(keyName) + ")"
        keyValue = "(\"" + "\", \"".join(keyValue) + "\")"
        query = "DELETE FROM " + table + " WHERE " + keyName + " = " + keyValue
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while deleting data from DB:\u0085\u0009" + str(e))

def nested_dict_pairs_iterator(dict_obj):
    ''' This function accepts a nested dictionary as argument
        and iterate over all values of nested dictionaries
    '''
    # Iterate over all key-value pairs of dict argument
    for key, value in dict_obj.items():
        # Check if value is of dict type
        if isinstance(value, dict):
            # If value is dict then iterate over all its values
            for pair in nested_dict_pairs_iterator(value):
                yield (key, *pair)
        else:
            # If value is not dict type then yield the value
            yield (key, value)

def fixJSONString(string):
    string = string.encode('unicode_escape').decode()
    string = string.replace(r"\\", "")
    string = string.replace(r']"', r"]")
    string = string.replace(r'"[', r'[')
    string = string.replace(r'"{', r'{')
    string = string.replace(r'}"', r'}')
    string = string.replace(r"'", r'"')
    return string

def DBQuery_to_dict(DBPath, query):
    try:
        conn = sq.connect(DBPath)
        conn.commit()
        result = pd.read_sql_query(query, conn)
        conn.close()

        data = result.to_json(orient="records")
        data = json.loads(fixJSONString(data))
        if(not isinstance(data, list)):
            data = [data]
        if (len(data) == 0):
            return [None]
        return data
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while querying DB:\u0085\u0009" + str(e))

def getIDs_fromDB(DBPath, table, keyName):
    query = "SELECT " + keyName + " FROM " + table
    result = [e[keyName] for e in DBQuery_to_dict(DBPath, query)]
    return result

def Ping(DBPath, table, KeyName, KeyValue):
    #TODO: get endpoints from DB and ping them
    return True


def istimeinstance(obj):
    try:
        datetime.strptime(obj, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False
    
def updateConnTable(DBPath, data, newStatus = None):
    try:
        table = data["table"]
        refID = data["refID"]
        connID = data["connID"]

        refValue = data["refValue"]
        connValues = data["connValues"]

        if(not check_presence_ofTableInDB(DBPath, table)):
            raise Client_Error_Handler.NotFound(message="Table \"" + table + "\" does not exist.")
        
        for keyName in [refID, connID]:
            if(not check_presence_ofColumnInDB(DBPath, table, keyName)):
                raise Client_Error_Handler.NotFound(message="The column \"" + keyName + "\" does not exist in the table \"" + table + "\"")
            
        if(not check_presence_inDB(DBPath, table, refID, refValue)):
            raise Client_Error_Handler.NotFound(status=400, message="The entry \"" + refValue + "\" of column \"" + refID + "\" does not exist in the table \"" + table + "\"")
        
        for connValue in connValues:
            entry = {
                refID : refValue,
                connID : connValue,
                "lastUpdate" : time.time()
            }
            if(newStatus != None):
                entry["Online"] = newStatus
            if(not check_presence_inDB(DBPath, table, [refID,connID], [refValue,connValue])):
                save_entry2DB(DBPath, table, entry)
            else:
                update_entry_inDB(DBPath, table, [refID,connID], entry)
    
    except HTTPError as e:
        raise HTTPError(status=e.status, message="An error occured while updating the connection table:\u0085\u0009" + e._message)
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occured while updating the connection table:\u0085\u0009" + str(e))

def isaMAC(value):
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return pattern.match(value)

def updateOnlineStatus(DBPath, params):
    try:
        table = params["table"]
        timer = params["timer"]

        if(not check_presence_ofTableInDB(DBPath, table)): 
            raise Client_Error_Handler.NotFound(message="The table \"" + table + "\" does not exist")
        
        now = time.time()
        query = "UPDATE " + table + " SET Online = 0 WHERE Online = 1 AND lastUpdate < " + str(now - timer)

        conn = sq.connect(DBPath)
        cursor = conn.cursor()
        cursor.execute(query)

        rowaffected = cursor.rowcount
        conn.commit()
        conn.close()

        return "Updated " + str(rowaffected) + " rows of table " + table + "." 
    except HTTPError as e:
        raise HTTPError(status=e.status, message ="An error occurred while updating the online status:\u0085\u0009" + e._message)
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occurred while updating the online status:\u0085\u0009" + str(e))
    
def setOnlineStatus(DBPath, params):
    try:
        table = params["table"]
        keyName = params["keyName"]
        keyValue = params["keyValue"]
        status = params["status"]

        if(not check_presence_ofTableInDB(DBPath, table)): 
            raise Client_Error_Handler.NotFound(message="The table \"" + table + "\" does not exist")
        
        if(not check_presence_ofColumnInDB(DBPath, table, keyName)):
            raise Client_Error_Handler.NotFound(message="The column \"" + keyName + "\" does not exist in the table \"" + table + "\"")
        
        if(not check_presence_inDB(DBPath, table, keyName, keyValue)):
            raise Client_Error_Handler.NotFound(message="The entry \"" + keyValue + "\" of column \"" + keyName + "\" does not exist in the table \"" + table + "\"")
        
        if(not (status in [0,1] or isinstance(status, bool))):
            raise Client_Error_Handler.BadRequest(message="The status must be either 0 or 1 or boolean")
        
        if(isinstance(status, bool)):
            status = int(status)
        
        query = "UPDATE " + table + " SET (Online, lastUpdate) = (" + str(status) + ", " + str(time.time()) + ") WHERE " + keyName + " = \"" + keyValue + "\""
        conn = sq.connect(DBPath)
        cursor = conn.cursor()
        cursor.execute(query)

        rowaffected = cursor.rowcount
        conn.commit()
        conn.close()

        return "Updated " + str(rowaffected) + " rows of table " + table + "." 
    except HTTPError as e:
        raise HTTPError(status=e.status, message ="An error occurred while setting the online status:\u0085\u0009" + e._message)
    except Exception as e:
        raise Server_Error_Handler.InternalServerError(message="An error occurred while setting the online status:\u0085\u0009" + str(e))
