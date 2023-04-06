from customErrors import *
import pandas as pd
import sqlite3 as sq
import json
import re
import time
from datetime import datetime

DBPath = "db.sqlite"
broker = "broker.hivemq.com"

def check_presence_inDB(DBPath, table, keyNames, keyValues):
    try:
        if(not isinstance(keyNames, list)) : keyNames = [keyNames]
        if(not isinstance(keyValues, list)) : keyValues = [keyValues]

        keyValues = [str(value) for value in keyValues]

        keyNames = "(" + ", ".join(keyNames) + ")"
        keyValues = "(\"" + "\", \"".join(keyValues) + "\")"

        query = "SELECT COUNT(*)>0 as result FROM " + table + " WHERE " + keyNames + " = " + keyValues
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"]) #True if the keyValue is present in the DB
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB:\n\t" + str(e))
    

def check_presence_ofColumnInDB(DBPath, table, columnName):
    try:
        query = "SELECT COUNT(*)>0 AS result FROM pragma_table_info(\"" + table + "\") WHERE name=\"" + columnName + "\""
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"])
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB:\n\t" + str(e))

def check_presence_ofTableInDB(DBPath, table):
    try:
        query = "SELECT COUNT(*)>0 AS result FROM sqlite_master WHERE (type, name) = (\"table\", \"" + table + "\")"
        return bool(DBQuery_to_dict(DBPath, query)[0]["result"])
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB:\n\t" + str(e))

def check_presence_inConnectionTables(DBPath, tables, keyName, keyValue):
    try:
        result = True
        for table in tables:
            if(check_presence_ofColumnInDB(DBPath, table, keyName)):
                result &= check_presence_inDB(DBPath, table, keyName, keyValue)
        
        return result               
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB:\n\t" + str(e))

def save_entry2DB(DBPath, table, entryData):
    try:
        conn = sq.connect(DBPath)
        query = "INSERT INTO " + table 
        query += "(\"" + "\", \"".join(entryData.keys()) + "\")"
        query += " VALUES "
        values = []
        for value in entryData.values():
            if(isinstance(value, list)):
                if(isinstance(value[0], int)):
                    value = [str(v) for v in value]
                else:
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
        raise web_exception(400, "An error occured while saving data to DB:\n\t" + str(e))

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
                    if(isinstance(value[0], int)):
                        value = [str(v) for v in value]
                    else:
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
        raise web_exception(400, str(e))

def delete_entry_fromDB(DBPath, table, keyNames, keyValues):
    try:
        if(not isinstance(keyNames, list)) : keyNames = [keyNames]
        if(not isinstance(keyValues, list)) : keyValues = [keyValues]

        keyValues = [str(value) for value in keyValues]

        conn = sq.connect(DBPath)

        keyNames = "(" + ", ".join(keyNames) + ")"
        keyValues = "(\"" + "\", \"".join(keyValues) + "\")"
        query = "DELETE FROM " + table + " WHERE " + keyNames + " = " + keyValues
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, "An error occured while deleting data from DB:\n\t" + str(e))

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
    conn = sq.connect(DBPath)
    result = pd.read_sql_query(query, conn)
    conn.close()

    data = result.to_json(orient="records")
    data = json.loads(fixJSONString(data))
    if(not isinstance(data, list)):
        data = [data]
    if (len(data) == 0):
        return [None]
    return data

def getIDs_fromDB(DBPath, table, keyName):
    query = "SELECT " + keyName + " FROM " + table
    result = [e[keyName] for e in DBQuery_to_dict(DBPath, query)]
    return result

def Ping(DBPath, table, KeyName, KeyValue):
    #TODO: get endpoints from DB and ping them
    return True


def istimeinstance(obj):
    try:
        datetime.strptime(obj, "%d/%m/%Y %H:%M")
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
            raise web_exception(400, "Table \"" + table + "\" does not exist.")
        
        for keyName in [refID, connID]:
            if(not check_presence_ofColumnInDB(DBPath, table, keyName)):
                raise web_exception(400, "The column \"" + keyName + "\" does not exist in the table \"" + table + "\"")
            
        if(not check_presence_inDB(DBPath, table, refID, refValue)):
            raise web_exception(400, "The entry \"" + refValue + "\" of column \"" + refID + "\" does not exist in the table \"" + table + "\"")
        
        for connValue in connValues:
            entry = {
                refID : refValue,
                connID : connValue,
                "lastUpdate" : datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            if(newStatus != None):
                entry["Online"] = newStatus
            if(not check_presence_inDB(DBPath, table, [refID,connID], [refValue,connValue])):
                save_entry2DB(DBPath, table, entry)
            else:
                update_entry_inDB(DBPath, table, [refID,connID], entry)
    
    except web_exception as e:
        raise web_exception(e.code, "An error occured while updating the connection table:\n\t" + e.message)
    except Exception as e:
        raise web_exception(400, "An error occured while updating the connection table:\n\t" + str(e))

            
