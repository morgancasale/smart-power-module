from endPoint import *
from resourceClass import *
from utility import *
from deviceScheduling import *

from cherrypy import HTTPError

class DeviceSettings:
    def __init__(self, settingsData, newSettings = False):
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
            raise HTTPError(status=400, message="Missing one or more keys")

    def checkAppl(self, applType): #TODO check if appliance exists in DB
        return check_presence_inDB(DBPath, "Appliances", "ApplianceType", applType)

    def checkSaveValues(self, settingsData):
        for key in settingsData.keys():
            match key:
                case ("deviceID" | "deviceName"):
                    if(not isinstance(settingsData[key], str)):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be string")
                    match key:
                        case "deviceID": self.deviceID = settingsData["deviceID"]
                        case "deviceName": self.deviceName = settingsData["deviceName"]

                case "enabledSockets":
                    if(not isinstance(settingsData[key], list) or len(settingsData[key]) != 3):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be a list of 3 values")
                    for socket in settingsData[key]:
                        if(not isinstance(socket, int) or socket not in [0, 1]):
                            raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be a list of booleans")
                    self.enabledSockets = settingsData["enabledSockets"]
                        
                    
                case ("HPMode" | "MPControl" | "faultControl" | "parControl" | "FBControl"):
                    if(isinstance(settingsData[key], int)):
                        settingsData[key] = bool(settingsData[key])
                    if(not isinstance(settingsData[key], bool)):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be boolean")
                    match key:
                        case "HPMode": self.HPMode = settingsData["HPMode"]
                        case "MPControl": self.MPControl = settingsData["MPControl"]
                        case "faultControl": self.faultControl = settingsData["faultControl"]
                        case "parControl": self.parControl = settingsData["parControl"]
                        case "FBControl": self.FBControl = settingsData["FBControl"]
                    
                case ("maxPower" | "parThreshold"):
                    if(not isinstance(settingsData[key], (int, float)) or settingsData[key] < 0):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be a positive float")
                    match key:
                        case "maxPower": self.maxPower = settingsData["maxPower"]
                        case "parThreshold": self.parThreshold = settingsData["parThreshold"]
                    
                case ("MPMode" | "FBMode"):
                    if(not isinstance(settingsData[key], str) or settingsData[key] not in ["null", "Notify", "Turn OFF"]):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be \"null\", \"Notify\" or \"Turn OFF\"")
                    match key:
                        case "MPMode": self.MPMode = settingsData["MPMode"]
                        case "FBMode": self.FBMode = settingsData["FBMode"]
                
                case "parMode":
                    if(not isinstance(settingsData[key], str) or settingsData[key] not in ["null", "Manual", "Auto"]):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be \"null\", \"Manual\" or \"Auto\"")
                    self.parMode = settingsData["parMode"]
                    
                case "applianceType":
                    if((not isinstance(settingsData[key], str)) or (not self.checkAppl(settingsData[key]))):
                        raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be a valid appliance type")
                    self.applianceType = settingsData["applianceType"]

                case "scheduling":
                    if(settingsData[key] is not None):
                        if(not isinstance(settingsData[key], list)):
                            raise HTTPError(status=400, message="Device settings' \"" + key + "\" value must be a list")
                        for sched in settingsData[key]:
                            if(not isinstance(sched, dict)):
                                raise HTTPError(status=400, message="Device settings' \"" + key + "\" list must contain only dictionaries")
                        
                            self.scheduling.append(DeviceSchedule(sched, newScheduling=True))

                case _:
                    raise HTTPError(status=400, message="Unexpected key \"" + key + "\"")

    def to_dict(self):
        result = {}
        for key in self.settingsKeys:
            if(key != "scheduling") : result[key] = getattr(self, key)
            
        return result

    def save2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise HTTPError(status=400, message="Device not found in DB")
            
            for sched in self.scheduling:
                sched.save2DB(DBPath, self.deviceID)

            update_entry_inDB(DBPath, "DeviceSettings", "deviceID", self.to_dict())
            update_entry_inDB(DBPath, "Devices", "deviceID", {"deviceID": self.deviceID, "deviceName": self.deviceName})

        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(500, "An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB:\n\t" + str(e))
        
    def updateDB(self, DBPath):
        self.save2DB(DBPath)

    def set2DB(self, DBPath):
        self.save2DB(DBPath)

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "DeviceSettings", "deviceID", params["deviceID"])):
                raise HTTPError(status=400, message="Settings for this device not found in DB")

            delete_entry_fromDB(DBPath, "DeviceSettings", params["deviceID"])
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while deleting device settings for device with ID \"" + params["deviceID"] + "\" from the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(500, "An error occurred while deleting device settings for device with ID \"" + params["deviceID"] + "\" from the DB:\n\t" + str(e))
        
    def cleanDB(DBPath):
        query = "SELECT * FROM DeviceSettings"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Devices", "deviceID", entry["deviceID"])):
                    DeviceSettings.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while cleaning device settings table:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while cleaning device settings table:\n\t" + str(e))
        
    
    def DB_to_dict(DBPath, device, verbose = True):
        try:
            deviceID = device["deviceID"]

            if(verbose):
                query = "SELECT * FROM DeviceSettings WHERE deviceID = \"" + deviceID + "\""
                devSettings = DBQuery_to_dict(DBPath, query)[0]
                devSettings["scheduling"] = DeviceSchedule.DB_to_dict(DBPath, deviceID)

            return devSettings
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while retrieving device settings for device with ID \"" + deviceID + "\" from the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(500, "An error occurred while retrieving device settings for device with ID \"" + deviceID + "\" from the DB:\n\t" + str(e))






