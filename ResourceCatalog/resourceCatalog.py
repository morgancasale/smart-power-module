import json
import pandas as pd
import sqlite3 as sq

from device import *
from user import *

class ResourceCatalog:
    def __init__(self, DBPath):
        self.DBPath = DBPath
    
    def handleGetRequest(self, cmd, params):
        try:
            match cmd:
                case "getInfo":
                    for entry in params:
                        return self.extractByKey(self.DBPath, entry["table"], entry["keyName"], entry["keyValue"])

                # case "getAllDevices":
                #     return self.extractByKey(self.DBPath, "Devices", "deviceID", "*")

                # case "getDeviceByID":
                #     return self.extractByKey(self.DBPath, "Devices", "deviceID", params)
                        
                # case "getAllUsers":
                #     return self.extractByKey(self.DBPath, "Users", "userID", "*")
                
                # case "getUserByID":
                #     return self.extractByKey(self.DBPath, "Users", "userID", params)
                    
                case "exit":
                    return self.exit(self.filename)

                case _:
                    raise web_exception(400, "Unexpected invalid command")
        except web_exception as e:
            raise web_exception(400, "An error occurred while handling the GET request: " + e.message)

    def handlePostRequest(self, cmd, params):
        try:
            match cmd:            
                case "regDevice":
                    for deviceData in params:
                        entry = Device(deviceData, newDevice = True)
                        entry.save2DB(self.DBPath)
                    return "Device registration was successful"

                case "regUser":
                    for userData in params:
                        entry = User(userData, newUser = True)
                        entry.save2DB(self.DBPath)
                    return "User registration was successful"
                    
                case "exit":
                    exit()

                case _:
                    raise web_exception(400, "The command \"" + cmd + "\" is not valid")
        except web_exception as e:
            raise web_exception(400, "An error occurred while handling the POST request: " + e.message)

    def handlePatchRequest(self, cmd, params):
        try:
            match cmd:
                case "updateDevice":
                    for deviceData in params:
                        entry = Device(deviceData)
                        entry.updateDB(self.DBPath)
                    return "Device update was successful"
                
                case "updateUser":
                    for userData in params:
                        entry = User(userData)
                        entry.updateDB(self.DBPath)
                    return "User update was successful"

                case "updateResource":
                    for resourceData in params:
                        entry = Resource(resourceData)
                        entry.updateDB(self.DBPath)
                    return "Resource update was successful"

                case "updateEndPoint":
                    for endPointData in params:
                        entry = EndPoint(endPointData)
                        entry.updateDB(self.DBPath)
                    return "EndPoint update was successful"
                
                case "exit":
                    exit()

                case _:
                    raise web_exception(400, "Unexpected invalid command")
        except web_exception as e:
            raise web_exception(400, "An error occurred while handling the PATCH request: " + e.message)

    def handleDeleteRequest(self, cmd, params):
        try:
            match cmd:
                case "delDevice":
                    for entry in params:
                        Device.deletefromDB(entry, self.DBPath)
                    return "Device deletion was successful"

                case "delUser":
                    for entry in params:
                        User.deletefromDB(entry, self.DBPath)
                    return "User deletion was successful"

                case "exit":
                    exit()

                case _:
                    raise web_exception(400, "Unexpected invalid command")
        except web_exception as e:
            raise web_exception(400, "An error occurred while handling the DELETE request: " + e.message)

    def reconstructJson(self, selectedData, table, DBPath):
        reconstructedData = []
        try:
            for sel in selectedData:
                match table:
                    case "Devices":
                        reconstructedData.append(Device.DB_to_dict(DBPath, sel))
                    case "Users":
                        reconstructedData.append(User.DB_to_dict(DBPath, sel))
                    case "Resources":
                        reconstructedData.append(Resource.DB_to_dict(DBPath, sel))
                    case "EndPoints":
                        reconstructedData.append(EndPoint.DB_to_dict(DBPath, sel))
                    case _:
                        raise web_exception(400, "Unexpected invalid table")
        except Exception as e:
            raise web_exception(400, e)

        return reconstructedData

    def extractByKey(DBPath, table, keyName, keyValue):
        selectedData = None
        if(not isinstance(keyValue, list)) : keyValue = [keyValue]

        if(not isinstance(keyName, str)):
            raise web_exception(400, "Key name must be a single string") 
        if(not all(isinstance(keyV, str) for keyV in keyValue)):
            raise web_exception(400, "Key values must be string")       
        if(not isinstance(table, str)):
            raise web_exception(400, "Table name must be single string")

        if(not isinstance(keyValue, list)) : keyValue = [keyValue]

        try:
            conn = sq.connect(DBPath)       
            if(keyValue[0] == "*"):
                query = "SELECT * FROM " + table
            else:
                query = "SELECT * FROM " + table + " WHERE " + keyName + " IN (\"" + "\", \"".join(keyValue) + "\")"
            
            selectedData = pd.read_sql_query(query, conn).to_dict(orient="records")
            conn.close()
        except Exception as e:
            raise web_exception(400, "An error occured while extracting data from DB: " + str(e))

        if len(selectedData) == 0:
            msg = "No entry found in table \"" + table
            msg += "\" with key " + keyName + " and values " + "[\"" + "\", \"".join(keyValue) + "\"]"
            raise web_exception(400, msg)

        reconstructedData = None
        try:
            reconstructedData = ResourceCatalog.reconstructJson(selectedData, table, DBPath) 
        except web_exception as e:
            raise web_exception(400, "An error occured while reconstructing data: " + e.message)
        except Exception as e:
            raise web_exception(400, "An error occured while reconstructing data: " + str(e))
        
        return json.dumps(reconstructedData)
        
