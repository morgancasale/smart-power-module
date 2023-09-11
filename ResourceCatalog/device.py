import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

import sqlite3 as sq

from endPoint import *
from resourceClass import *
from utility import *

from microserviceBase.Error_Handler import *

class Device:
    def __init__(self, deviceData, newDevice = False):
        self.deviceKeys = ["deviceID", "deviceName", "endPoints", "Resources"]

        self.endPoints = []
        self.Resources = []

        self.userID = None

        if(newDevice) : self.checkKeys(deviceData)
        self.checkSaveValues(deviceData)

        if(newDevice): 
            self.Online = True
            self.lastUpdate = time.time()
        

    def checkKeys(self, deviceData):
        if(not all(key in self.deviceKeys for key in deviceData.keys())): # Check if all keys of deviceKeys are present in deviceData
            raise Client_Error_Handler.BadRequest(message="Missing one or more keys")

    def checkSaveValues(self, deviceData):
        for key in deviceData.keys():
            match key:
                case ("deviceID" | "deviceName" | "userID"):
                    if(not isinstance(deviceData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="Device's \"" + key + "\" value must be string")
                    match key:
                        case "deviceID": self.deviceID = deviceData["deviceID"]
                        case "deviceName": self.deviceName = deviceData["deviceName"]
                        case "userID": self.userID = deviceData["userID"]
                    
                case "endPoints":
                    for endPointData in deviceData["endPoints"]:
                        try:
                            self.endPoints.append(EndPoint(endPointData, newEndPoint = True))
                        except HTTPError as e:
                            raise HTTPError(status=e.status, message ="EndPoint with ID " + endPointData["endPointID"] + " not valid:\u0085\u0009" + e._message)
                case "Resources":
                    for resourceData in deviceData["Resources"]:
                        try:
                            self.Resources.append(Resource(resourceData, newResource = True))
                        except HTTPError as e:
                            raise HTTPError(status=e.status, message ="Resource with ID " + resourceData["resourceID"] + " not valid:\u0085\u0009" + e._message)
                case _:
                    raise Client_Error_Handler.BadRequest(message="Unexpected key \"" + key + "\"")

    def to_dict(self):
        return {"deviceID": self.deviceID, "deviceName": self.deviceName, "lastUpdate": self.lastUpdate, 
                "Online": self.Online}

    def save2DB(self, DBPath):
        EP_Dev_conn = []
        Res_Dev_conn = []
        try:
            if(check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise Client_Error_Handler.BadRequest(message="A device with ID \"" + self.deviceID + "\" already exists in the database")
            if(self.userID != None and not check_presence_inDB(DBPath, "Users", "userID", self.userID)):
                raise Client_Error_Handler.NotFound(message="The user with ID \"" + self.userID + "\" does not exist in the database")            

            for endPoint in self.endPoints:
                endPoint.set2DB(DBPath)
                EP_Dev_conn.append(endPoint.endPointID)

            for resource in self.Resources:
                resource.set2DB(DBPath)
                Res_Dev_conn.append(resource.resourceID)

            # Save the device to the DB
            self.Online = self.Ping()

            # Save the connection between the device and the user
            # save_entry2DB(DBPath, "UserDevice_conn", {"userID": self.userID, "deviceID": self.deviceID})
            # Save the connection between the device and the endpoints
            for EPID in EP_Dev_conn:
                entry = {"deviceID": self.deviceID, "endPointID": EPID, "lastUpdate": self.lastUpdate}
                save_entry2DB(DBPath, "DeviceEndP_conn", entry)

            # Save the connection between the device and the resources
            for ResID in Res_Dev_conn:
                entry = {"deviceID": self.deviceID, "resourceID": ResID, "Online": self.Online, "lastUpdate": self.lastUpdate}
                save_entry2DB(DBPath, "DeviceResource_conn", entry)
            
            save_entry2DB(DBPath, "Devices", self.to_dict())
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message ="An error occurred while saving device with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving device with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def updateDB(self, DBPath):
        endPointIDs = []
        resourceIDs = []

        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise Client_Error_Handler.NotFound(message="The device with ID \"" + self.deviceID + "\" does not exist in the database")

            self.Online = True
            self.lastUpdate = time.time()

            for endPoint in self.endPoints:
                try:
                    endPoint.set2DB(DBPath)
                except HTTPError as e:
                    message = "An error occurred while updating device's endpoint with ID \"" + endPoint.endPointID + "\":\u0085\u0009" + str(e._message)
                    raise HTTPError(status=e.status, message = message)
                except Exception as e:
                    message = "An error occurred while updating device's endpoint with ID \"" + endPoint.endPointID + "\":\u0085\u0009" + str(e)
                    raise Server_Error_Handler.InternalServerError(message = message)
                endPointIDs.append(endPoint.endPointID)

            for resource in self.Resources:
                try:
                    resource.set2DB(DBPath)
                except HTTPError as e:
                    message = "An error occurred while updating device's resource with ID \"" + resource.resourceID + "\":\u0085\u0009" + str(e._message)
                    raise HTTPError(status=e.status, message=message)
                except Exception as e:
                    message = "An error occurred while updating device's resource with ID \"" + resource.resourceID + "\":\u0085\u0009" + str(e)
                    raise Server_Error_Handler.InternalServerError(message=message)
                resourceIDs.append(resource.resourceID)

            if(len(endPointIDs)>0):
                data = {"table" : "DeviceEndP_conn", "refID" : "deviceID", "connID" : "endPointID", "refValue" : self.deviceID, "connValues" : endPointIDs}
                updateConnTable(DBPath, data)
                
            if(len(resourceIDs)>0):
                data = {"table" : "DeviceResource_conn", "refID" : "deviceID", "connID" : "resourceID", "refValue" : self.deviceID, "connValues" : resourceIDs}
                updateConnTable(DBPath, data, self.Online)
            
            update_entry_inDB(DBPath, "Devices", "deviceID", self.to_dict())   
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while updating device with ID \"" + 
                self.deviceID + "\" in the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while updating device with ID \"" + 
                self.deviceID + "\" in the DB:\u0085\u0009" + str(e)
            )

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving device with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving device with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )
    
    def DB_to_dict(DBPath, device, verbose = True):
        try:
            deviceID = device["deviceID"]

            deviceData = {"deviceID": deviceID, "deviceName": device["deviceName"], "lastUpdate": device["lastUpdate"], "Online": bool(device["Online"])}

             
            deviceData = {"deviceID": deviceID, "deviceName": device["deviceName"], "endPoints": [], "Resources": [], "lastUpdate": device["lastUpdate"], "Online": bool(device["Online"])}
            query = "SELECT * FROM DeviceEndP_conn WHERE deviceID = \"" + deviceID + "\""
            result = DBQuery_to_dict(DBPath, query)
            for EP in result:
                if(verbose):
                    deviceData["endPoints"].append(EndPoint.DB_to_dict(DBPath, EP))
                else:
                    deviceData["endPoints"].append(EP["endPointID"])

            query = "SELECT * FROM DeviceResource_conn WHERE deviceID = \"" + deviceID + "\""
            result = DBQuery_to_dict(DBPath, query)
            for resource in result:
                if(verbose):
                    deviceData["Resources"].append(Resource.DB_to_dict(DBPath, resource, {"deviceID": deviceID}))
                else:
                    deviceData["Resources"].append(resource["resourceID"])
                    
            return deviceData
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while retrieving device with ID \"" + 
                deviceID + "\" from the DB:\u0085\u0009" + str(e)
            )

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", params["deviceID"])):
                raise HTTPError(status=400, message="The device with ID \"" + params["deviceID"] + "\" does not exist in the database")

            '''delete_entry_fromDB(DBPath, "UserDevice_conn", "deviceID", params["deviceID"])
            delete_entry_fromDB(DBPath, "DeviceEndP_conn", "deviceID", params["deviceID"])
            EndPoint.cleanDB(DBPath)
            delete_entry_fromDB(DBPath, "DeviceResource_conn", "deviceID", params["deviceID"])
            Resource.cleanDB(DBPath)'''
            delete_entry_fromDB(DBPath, "Devices", "deviceID", params["deviceID"])

            return True
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while deleting the device with ID \"" + 
                params["deviceID"] + "\" from the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while deleting the device with ID \"" + 
                params["deviceID"] + "\" from the DB:\u0085\u0009" + str(e)
            )

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        connTables = ["UserDevice_conn"]

        query = "SELECT * FROM Devices"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inConnectionTables(DBPath, connTables, "deviceID", entry["deviceID"])):
                    Device.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while cleaning the DB from devices:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while cleaning the DB from devices:\u0085\u0009" + str(e))

    def setOnlineStatus(entries):
        newDeviceIDs = []
        newEndPointIDs = []
        newResourceIDs = []
        
        if(not isinstance(entries, list)): entries = [entries]
        try:
            for entry in entries:
                newDeviceIDs.append(entry.deviceID)
                newEndPointIDs.extend([e.endPointID for e in entry.endPoints])
                newResourceIDs.extend([r.resourceID for r in entry.Resources])

            allDeviceIDs = getIDs_fromDB(DBPath, "Devices", "deviceID")

            missingDeviceIDs = list(set(allDeviceIDs) - set(newDeviceIDs))

            entry = {"deviceID": missingDeviceIDs, "Online": False, "lastUpdate": time.time()}

            update_entry_inDB(DBPath, "Devices", "deviceID", entry)
            EndPoint.setOnlineStatus(newEndPointIDs)
            Resource.setOnlineStatus(newResourceIDs, "DeviceResource_conn")
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while setting the online status of devices:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while setting the online status of devices:\u0085\u0009" + str(e))
    
    def Ping(self):
        #TODO check devices that use this endpoint, ping them and return True if at least one is online
        return True
    