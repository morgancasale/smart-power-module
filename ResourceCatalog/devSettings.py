import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from endPoint import *
from resourceClass import *
from utility import *
from deviceScheduling import *

from cherrypy import HTTPError

from microserviceBase.Error_Handler import *
class DeviceSettings:
    def __init__(self, settingsData, newSettings = True):
        self.settingsKeys = [
            "deviceID", "deviceName", "enabledSockets", "HPMode", "MPControl", "maxPower", "MPMode", "faultControl",
            "parControl", "parThreshold", "parMode", "applianceType", "FBControl", "FBMode",
            "scheduling"
        ]

        self.scheduling = []

        if(newSettings) : self.checkKeys(settingsData)
        self.checkSaveValues(settingsData)
        

    def checkKeys(self, settingsData):
        if(not all(key in self.settingsKeys for key in settingsData.keys())): # Check if all keys of settingsKeys are present in deviceData
            raise Client_Error_Handler.BadRequest("Missing one or more keys")

    def checkAppl(self, applType): #TODO check if appliance exists in DB
        try:
            if(applType == "None"): return True
            return check_presence_inDB(DBPath, "AppliancesInfo", "ApplianceType", applType)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message=e._message
            )

    def checkSaveValues(self, settingsData):
        for key in settingsData.keys():
            match key:
                case ("deviceID" | "deviceName"):
                    if(not isinstance(settingsData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be string")
                    match key:
                        case "deviceID": self.deviceID = settingsData["deviceID"]
                        case "deviceName": self.deviceName = settingsData["deviceName"]

                case "enabledSockets":
                    if(not isinstance(settingsData[key], list) or len(settingsData[key]) != 3):
                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be a list of 3 values")
                    for socket in settingsData[key]:
                        if(not isinstance(socket, int) or socket not in [0, 1]):
                            raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be a list of booleans")
                    self.enabledSockets = settingsData["enabledSockets"]
                        
                    
                case ("HPMode" | "MPControl" | "faultControl" | "parControl" | "FBControl"):
                    if(isinstance(settingsData[key], int)):
                        settingsData[key] = bool(settingsData[key])
                    if(not isinstance(settingsData[key], bool)):
                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be boolean")
                    match key:
                        case "HPMode": self.HPMode = settingsData["HPMode"]
                        case "MPControl": self.MPControl = settingsData["MPControl"]
                        case "faultControl": self.faultControl = settingsData["faultControl"]
                        case "parControl": self.parControl = settingsData["parControl"]
                        case "FBControl": self.FBControl = settingsData["FBControl"]
                    
                case ("maxPower" | "parThreshold"):
                    if(not isinstance(settingsData[key], (int, float)) or settingsData[key] < 0):
                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be a positive number")
                    match key:
                        case "maxPower": self.maxPower = settingsData["maxPower"]
                        case "parThreshold": self.parThreshold = settingsData["parThreshold"]
                    
                case ("MPMode" | "FBMode"):
                    if(not isinstance(settingsData[key], str) or settingsData[key] not in ["null", "Notify", "Turn OFF"]):
                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be \"null\", \"Notify\" or \"Turn OFF\"")
                    match key:
                        case "MPMode": self.MPMode = settingsData["MPMode"]
                        case "FBMode": self.FBMode = settingsData["FBMode"]
                
                case "parMode":
                    if(not isinstance(settingsData[key], str) or settingsData[key] not in ["null", "Manual", "Auto"]):
                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be \"null\", \"Manual\" or \"Auto\"")
                    self.parMode = settingsData["parMode"]
                    
                case "applianceType":
                    if(settingsData[key] is not None):
                        if((not isinstance(settingsData[key], str)) or (not self.checkAppl(settingsData[key]))):
                            raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be a valid appliance type")
                        self.applianceType = settingsData["applianceType"]

                case "scheduling":
                    if(settingsData[key] is not None):
                        if(not isinstance(settingsData[key], list)):
                            raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" value must be a list")
                        for socketScheds in settingsData[key]:
                            if(socketScheds is not None):
                                if(not isinstance(socketScheds, list)):
                                    raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" schedules must contain only lists")
                                for sched in socketScheds:
                                    if(not isinstance(sched, dict)):
                                        raise Client_Error_Handler.BadRequest(message="Device settings' \"" + key + "\" list must contain only dictionaries")

                                    sched.update({"deviceID": self.deviceID})
                                    self.scheduling.append(DeviceSchedule(sched, newSchedule=True))

                case _:
                    raise Client_Error_Handler.BadRequest(message="Unexpected key \"" + key + "\"")

    def to_dict(self):
        result = {}
        for key in self.settingsKeys:
            if(key != "scheduling") : result[key] = getattr(self, key)
            
        return result

    def updateNameinHA(self): #TODO Test this 
        try:
            query = "SELECT * FROM DeviceSettings WHERE deviceID = \"" + self.deviceID + "\""
            devSettings = DBQuery_to_dict(DBPath, query)[0]

            if(devSettings["deviceName"] != self.deviceName):
                query = "SELECT * FROM EndPoints WHERE endPointName = \"deviceConnector\""
                deviceConnector = DBQuery_to_dict(DBPath, query)[0]

                url = "http://%s:%s/updateDeviceName" % (deviceConnector["IPAddress"], deviceConnector["port"])
                headers = {"Content-Type": "application/json"}
                data = {"deviceID": self.deviceID, "deviceName": self.deviceName}

                response = requests.put(url, headers=headers, data=json.dumps(data))
                if(response.status_code != 200):
                    raise HTTPError(status=response.status_code, message=response.text)
                
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while updating device name for device with ID \"" + 
                self.deviceID + "\" in HA:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while updating device name for device with ID \"" + 
                self.deviceID + "\" in HA:\u0085\u0009" + str(e)
            )


        
    
    def save2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise Client_Error_Handler.NotFound(message="Device not found in DB")
            
            for sched in self.scheduling:
                sched.save2DB(DBPath)
            
            save_entry2DB(DBPath, "DeviceSettings", self.to_dict())

        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )
        
    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise Client_Error_Handler.NotFound(message="Device not found in DB")
            
            for sched in self.scheduling:
                sched.save2DB(DBPath)

            update_entry_inDB(DBPath, "DeviceSettings", "deviceID", self.to_dict())
            
            update_entry_inDB(DBPath, "Devices", "deviceID", {"deviceID": self.deviceID, "deviceName": self.deviceName})

        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )

    def set2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "DeviceSettings", "deviceID", self.deviceID)):
                self.updateDB(DBPath)
            else:
                self.save2DB(DBPath)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while setting device settings for device with ID \"" + 
                self.deviceID + "\" to the DB:\u0085\u0009" + str(e._message)
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while setting device settings for device with ID \"" + self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )
        

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "DeviceSettings", "deviceID", params["deviceID"])):
                raise Client_Error_Handler.NotFound(message="Settings for this device not found in DB")

            delete_entry_fromDB(DBPath, "DeviceSettings", params["deviceID"])
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while deleting device settings for device with ID \"" + params["deviceID"] + "\" from the DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while deleting device settings for device with ID \"" + params["deviceID"] + "\" from the DB:\u0085\u0009" + str(e)
            )
           
    def cleanDB(DBPath):
        query = "SELECT * FROM DeviceSettings"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Devices", "deviceID", entry["deviceID"])):
                    DeviceSettings.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while cleaning device settings table:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError("An error occurred while cleaning device settings table:\u0085\u0009" + str(e))
        
    
    def DB_to_dict(DBPath, device):
        try:
            deviceID = device["deviceID"]
            query = "SELECT * FROM DeviceSettings WHERE deviceID = \"" + deviceID + "\""
            devSettings = DBQuery_to_dict(DBPath, query)[0]
            devSettings["scheduling"] = DeviceSchedule.DB_to_dict(DBPath, deviceID)

            return devSettings
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while retrieving device settings for device with ID \"" + deviceID + "\" from the DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                "An error occurred while retrieving device settings for device with ID \"" + deviceID + "\" from the DB:\u0085\u0009" + str(e)
            )