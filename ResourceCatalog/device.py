import sqlite3 as sq

from endPoint import *
from resourceClass import *
from utility import *

class Device:
    def __init__(self, deviceData, newDevice = False):
        self.deviceKeys = ["deviceID", "deviceName", "endPoints", "Resources"]

        self.endPoints = []
        self.Resources = []

        if(newDevice) : self.checkKeys(deviceData)
        self.checkSaveValues(deviceData)

        if(newDevice): 
            self.Online = True
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        

    def checkKeys(self, deviceData):
        if(not all(key in self.deviceKeys for key in deviceData.keys())): # Check if all keys of deviceKeys are present in deviceData
            raise web_exception(400, "Missing one or more keys")

    def checkSaveValues(self, deviceData):
        for key in deviceData.keys():
            match key:
                case ("deviceID" | "deviceName" | "userID"):
                    if(not isinstance(deviceData[key], str)):
                        raise web_exception(400, "Device's \"" + key + "\" value must be string")
                    match key:
                        case "deviceID": self.deviceID = deviceData["deviceID"]
                        case "deviceName": self.deviceName = deviceData["deviceName"]
                        case "userID": self.userID = deviceData["userID"]
                    
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
        return {"deviceID": self.deviceID, "deviceName": self.deviceName, "lastUpdate": self.lastUpdate, 
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
            self.Online = self.Ping()
            save_entry2DB(DBPath, "Devices", self.to_dict())

            # Save the connection between the device and the user
            #save_entry2DB(DBPath, "UserDevice_conn", {"userID": self.userID, "deviceID": self.deviceID})
            # Save the connection between the device and the endpoints
            for EPID in EP_Dev_conn:
                entry = {"deviceID": self.deviceID, "endPointID": EPID,
                         "lastUpdate": self.lastUpdate
                        }
                save_entry2DB(DBPath, "DeviceEndP_conn", entry)
            # Save the connection between the device and the resources
            for ResID in Res_Dev_conn:
                entry = {"deviceID": self.deviceID, "resourceID": ResID, 
                         "Online": self.Online, "lastUpdate": self.lastUpdate
                        }
                save_entry2DB(DBPath, "DeviceResource_conn", entry)
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving device with ID \"" + self.deviceID + "\" to the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving device with ID \"" + self.deviceID + "\" to the DB: " + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise web_exception(400, "The device with ID \"" + self.deviceID + "\" does not exist in the database")

            self.Online = True
            self.lastUpdate = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            update_entry_inDB(DBPath, "Devices", "deviceID", self.to_dict())   
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating device with ID \"" + self.deviceID + "\" in the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while updating device with ID \"" + self.deviceID + "\" in the DB: " + str(e))

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving device with ID \"" + self.deviceID + "\" to the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving device with ID \"" + self.deviceID + "\" to the DB: " + str(e))
    
    def DB_to_dict(DBPath, device, verbose = True):
        try:
            deviceID = device["deviceID"]

            deviceData = {"deviceID": deviceID, "deviceName": device["deviceName"], "lastUpdate": device["lastUpdate"], "Online": bool(device["Online"])}

            if(verbose):  
                deviceData = {"deviceID": deviceID, "deviceName": device["deviceName"], "endPoints": [], "Resources": [], "lastUpdate": device["lastUpdate"], "Online": bool(device["Online"])}
                query = "SELECT * FROM DeviceEndP_conn WHERE deviceID = \"" + deviceID + "\""
                result = DBQuery_to_dict(DBPath, query)
                for EP in result:
                    deviceData["endPoints"].append(EndPoint.DB_to_dict(DBPath, EP))

                query = "SELECT * FROM DeviceResource_conn WHERE deviceID = \"" + deviceID + "\""
                result = DBQuery_to_dict(DBPath, query)
                for resource in result:
                    deviceData["Resources"].append(Resource.DB_to_dict(DBPath, resource, {"deviceID": deviceID}))

            return deviceData
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving device with ID \"" + deviceID + "\" from the DB: " + str(e))

    def deleteFromDB(DBPath, params):
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
        
        return True

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        connTables = ["UserDevice_conn"]

        query = "SELECT * FROM Devices"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inConnectionTables(DBPath, connTables, "deviceID", entry["deviceID"])):
                    Device.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})
        except web_exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from devices: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from devices: " + str(e))

    def setOnlineStatus(entries):
        newDeviceIDs = []
        newEndPointIDs = []
        newResourceIDs = []

        for entry in entries:
            newDeviceIDs.append(entry.deviceID)
            newEndPointIDs.extend([e.endPointID for e in entry.endPoints])
            newResourceIDs.extend([r.resourceID for r in entry.Resources])

        allDeviceIDs = getIDs_fromDB(DBPath, "Devices", "deviceID")

        missingDeviceIDs = list(set(allDeviceIDs) - set(newDeviceIDs))

        entry = {"deviceID": missingDeviceIDs, "Online": False, "lastUpdate": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

        update_entry_inDB(DBPath, "Devices", "deviceID", entry)
        EndPoint.setOnlineStatus(newEndPointIDs)
        Resource.setOnlineStatus(newResourceIDs, "DeviceResource_conn")
    
    def Ping(self):
        #TODO check devices that use this endpoint, ping them and return True if at least one is online
        return True
    