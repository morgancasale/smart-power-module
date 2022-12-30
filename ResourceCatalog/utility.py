from customErrors import *
import pandas as pd
import sqlite3 as sq
import json
import re
import datetime

def check_presence_inDB(DBPath, table, keyName, keyValue):
    try:
        query = "SELECT * FROM " + table + " WHERE " + keyName + " = \"" + keyValue + "\""
        selectedData = DBQuery_to_dict(DBPath, query)

        return (len(selectedData) != 0) #True if the keyValue is present in the DB
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))
    

def check_presence_ofColumnInDB(DBPath, table, columnName):
    try:
        query = "SELECT COUNT(*) AS cnt FROM pragma_table_info(\"" + table + "\") WHERE name=\"" + columnName + "\""
        return bool(DBQuery_to_dict(DBPath, query)[0]["cnt"])
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))

def check_presence_inConnectionTables(DBPath, tables, keyName, keyValue):
    try:
        result = True
        for table in tables:
            if(check_presence_ofColumnInDB(DBPath, table, keyName)):
                result &= check_presence_inDB(DBPath, table, keyName, keyValue)
        
        return result               
    except Exception as e:
        raise web_exception(400, "An error occured while extracting data from DB: " + str(e))

def save_entry2DB(DBPath, table, entryData):
    try:
        conn = sq.connect(DBPath)
        query = "INSERT INTO " + table 
        query += "(\"" + "\", \"".join(entryData.keys()) + "\")"
        query += " VALUES "
        values = []
        for value in entryData.values():
            if(isinstance(value, list)):
                value = values.append(str(value))
            if(value == None):
                value = values.append("NULL")
        query += "(\"" + "\", \"".join(values) + "\")"

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, "An error occured while saving data to DB: " + str(e))

def update_entry_inDB(DBPath, table, keyName, entryData):
    try:
        conn = sq.connect(DBPath)
        query = "UPDATE " + table + " SET "
    
        keys = "(" + list(entryData.keys()).join(", ")+")"
        query += keys + " = "

        values = None
        for value in entryData.values():
            if(isinstance(value, list)):
                value = str(value)
            if(value == None):
                value = "NULL"
            values.append(value)
        values = "(" + values.join(", ") + ")"
        query += values

        query += " WHERE " + keyName + " = \"" + entryData[keyName] + "\""

        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, "An error occured while updating data in DB: " + str(e))

def delete_entry_fromDB(DBPath, table, keyName, keyValue):
    try:
        conn = sq.connect(DBPath)
        query = "DELETE FROM " + table + " WHERE " + keyName + " = \"" + keyValue + "\""
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        raise web_exception(400, "An error occured while deleting data from DB: " + str(e))

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

def fix_jsonString(string):
    string = string.encode('unicode_escape').decode()
    string = string.replace(r"\\", "")
    string = string.replace(r']"', r"]")
    string = string.replace(r'"[', r'[')
    string = string.replace(r"'", r'"')
    return string

def DBQuery_to_dict(DBPath, query):
    conn = sq.connect(DBPath)
    result = pd.read_sql_query(query, conn)
    conn.close()

    data = result.to_json(orient="records")
    data = json.loads(fix_jsonString(data))
    return data