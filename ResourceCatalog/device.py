import sqlite3 as sq

from endPoint import *
from resourceClass import *
from utility import *

class Device:
    def __init__(self, deviceData, newDevice = False):
        self.deviceKeys = ["deviceID", "Name", "userID", "endPoints", "Resources"]

        self.endPoints = []
        self.Resources = []

        if(newDevice) : self.checkKeys(deviceData)
        self.checkSaveValues(deviceData)

        if(newDevice): 
            self.Online = self.Ping(DBPath, "Devices", "deviceID", self.deviceID)
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        

    def checkKeys(self, deviceData):
        if(not all(key in self.deviceKeys[0:2] for key in deviceData.keys())): # Check if all keys of deviceKeys are present in deviceData
            raise web_exception(400, "Missing one or more keys")

    def checkSaveValues(self, deviceData):
        for key in deviceData.keys():
            match key:
                case ("deviceID" | "Name" | "userID"):
                    if(not isinstance(deviceData[key], str)):
                        raise web_exception(400, "Device's \"" + key + "\" value must be string")
                    match key:
                        case "deviceID":
                            self.deviceID = deviceData["deviceID"]
                        case "Name":
                            self.Name = deviceData["Name"]
                        case "userID":
                            self.userID = deviceData["userID"]
                    
                case "endPoints":
                    for endPointData in deviceData["endPoints"]:
                        try:
                            self.endPoints.append(EndPoint(endPointData, newEndPoint = True))
                        except web_exception as e:
                            raise web_exception(400, "EndPoint with ID " + endPointData["endPointID"] + " not valid: " + e.message)
                case "Resources":
                    for resourceData in deviceData["Resources"]:
                        try:
                            self.Resources.append(Resource(resourceData, newResource = True))
                        except web_exception as e:
                            raise web_exception(400, "Resource with ID " + resourceData["resourceID"] + " not valid: " + e.message)
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")

    def to_dict(self):
        return {"deviceID": self.deviceID, "Name": self.Name, "lastUpdate": self.lastUpdate, 
                "Online": self.Online}

    def save2DB(self, DBPath):
        EP_Dev_conn = []
        Res_Dev_conn = []
        
        try:
            if(not check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise web_exception(400, "The user with ID \"" + self.userID + "\" does not exist in the database")

            if(check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise web_exception(400, "A device with ID \"" + self.deviceID + "\" already exists in the database")

            for endPoint in self.endPoints:
                endPoint.save2DB(DBPath)
                EP_Dev_conn.append(endPoint.endPointID)

            for resource in self.Resources:
                resource.save2DB(DBPath)
                Res_Dev_conn.append(resource.resourceID)

            # Save the device to the DB
            self.Online = self.Ping(self.endPoints)
            save_entry2DB(DBPath, "Devices", self.to_dict())

            # Save the connection between the device and the user
            save_entry2DB(DBPath, "UserDevice_conn", {"userID": self.userID, "deviceID": self.deviceID})
            # Save the connection between the device and the endpoints
            for entry in EP_Dev_conn:
                save_entry2DB(DBPath, "DeviceEndP_conn", {"deviceID": self.deviceID, "endPointID": entry})
            # Save the connection between the device and the resources
            for entry in Res_Dev_conn:
                save_entry2DB(DBPath, "DeviceResource_conn", {"deviceID": self.deviceID, "resourceID": entry})
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving device with ID \"" + self.deviceID + "\" to the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving device with ID \"" + self.deviceID + "\" to the DB: " + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise web_exception(400, "The device with ID \"" + self.deviceID + "\" does not exist in the database")

            self.Online = Ping(DBPath, "Devices", "deviceID", self.deviceID)
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            update_entry_inDB(DBPath, "Devices", "deviceID", self.to_dict())   
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating device with ID \"" + self.deviceID + "\" in the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while updating device with ID \"" + self.deviceID + "\" in the DB: " + str(e))

    def DB_to_dict(DBPath, device):
        try:
            deviceID = device["deviceID"]

            deviceData = {"deviceID": deviceID, "Name": device["Name"], "endPoints": [], "Resources": [], "lastUpdate": device["lastUpdate"], "Online": bool(device["Online"])}
            
            query = "SELECT * FROM DeviceEndP_conn WHERE deviceID = \"" + deviceID + "\""
            result = DBQuery_to_dict(DBPath, query)
            for EP in result:
                deviceData["endPoints"].append(EndPoint.DB_to_dict(DBPath, EP))

            query = "SELECT * FROM DeviceResource_conn WHERE deviceID = \"" + deviceID + "\""
            result = DBQuery_to_dict(DBPath, query)
            for resource in result:
                deviceData["Resources"].append(Resource.DB_to_dict(DBPath, resource))

            return deviceData
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving device with ID \"" + deviceID + "\" from the DB: " + str(e))

    def deletefromDB(params, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", params["deviceID"])):
                raise web_exception(400, "The device with ID \"" + params["deviceID"] + "\" does not exist in the database")

            delete_entry_fromDB(DBPath, "UserDevice_conn", "deviceID", params["deviceID"])
            delete_entry_fromDB(DBPath, "DeviceEndP_conn", "deviceID", params["deviceID"])
            EndPoint.cleanDB(DBPath)
            delete_entry_fromDB(DBPath, "DeviceResource_conn", "deviceID", params["deviceID"])
            Resource.cleanDB(DBPath)
            delete_entry_fromDB(DBPath, "Devices", "deviceID", params["deviceID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting the device with ID \"" + params["deviceID"] + "\" from the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while deleting the device with ID \"" + params["deviceID"] + "\" from the DB: " + str(e))

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        connTables = ["UserDevice_conn"]

        query = "SELECT * FROM Devices"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inConnectionTables(DBPath, connTables, "deviceID", entry["deviceID"])):
                    Device.deletefromDB({"deviceID": entry["deviceID"]}, DBPath)
        except web_exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from devices: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from devices: " + str(e))
    