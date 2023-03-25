import sqlite3 as sq

from endPoint import *
from resourceClass import *
from utility import *
from deviceScheduling import *

class DeviceSettings:
    def __init__(self, settingsData, newSettings = False):
        self.settingsKeys = ["deviceID", "deviceName", "HPMode", "MPControl", "maxPower", "MPMode", "faultControl",
                             "parControl", "parThreshold", "parMode", "applianceType", "FBControl", "FBMode",
                             "scheduling"]

        self.scheduling = []

        if(newSettings) : self.checkKeys(settingsData)
        self.checkSaveValues(settingsData)
        

    def checkKeys(self, settingsData):
        if(not all(key in self.settingsKeys for key in settingsData.keys())): # Check if all keys of settingsKeys are present in deviceData
            raise web_exception(400, "Missing one or more keys")

    def checkAppl(self, applType): #TODO check if appliance exists in DB
        return True

    def checkSaveValues(self, settingsData):
        for key in settingsData.keys():
            match key:
                case ("deviceID" | "deviceName"):
                    if(not isinstance(settingsData[key], str)):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be string")
                    match key:
                        case "deviceID": self.deviceID = settingsData["deviceID"]
                        case "deviceName": self.deviceName = settingsData["deviceName"]
                    
                case ("HPMode" | "MPControl" | "faultControl" | "parControl" | "FBControl"):
                    if(not isinstance(settingsData[key], bool)):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be boolean")
                    match key:
                        case "HPMode": self.HPMode = settingsData["HPMode"]
                        case "MPControl": self.MPControl = settingsData["MPControl"]
                        case "faultControl": self.faultControl = settingsData["faultControl"]
                        case "parControl": self.parControl = settingsData["parControl"]
                        case "FBControl": self.FBControl = settingsData["FBControl"]
                    
                case ("maxPower" | "parThreshold"):
                    if(not isinstance(settingsData[key], float) or settingsData[key] < 0):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be a positive float")
                    match key:
                        case "maxPower": self.maxPower = settingsData["maxPower"]
                        case "parThreshold": self.parThreshold = settingsData["parThreshold"]
                    
                case ("MPMode" | "FBMode"):
                    if(not isinstance(settingsData[key], str) or settingsData[key] not in ["null", "Notify", "TurnOff"]):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be \"null\", \"Notify\" or \"TurnOff\"")
                    match key:
                        case "MPMode": self.MPMode = settingsData["MPMode"]
                        case "FBMode": self.FBMode = settingsData["FBMode"]
                
                case "parMode":
                    if(not isinstance(settingsData[key], str) or settingsData[key] not in ["null", "Manual", "Auto"]):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be \"null\", \"Manual\" or \"Auto\"")
                    self.parMode = settingsData["parMode"]
                    
                case "applianceType":
                    if(not isinstance(settingsData[key], str) or self.checkAppl(settingsData[key])):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be a valid appliance type")
                    self.applianceType = settingsData["applianceType"]

                case "scheduling":
                    if(not isinstance(settingsData[key], list)):
                        raise web_exception(400, "Device settings' \"" + key + "\" value must be a list")
                    for sched in settingsData[key]:
                        if(not isinstance(sched, dict)):
                            raise web_exception(400, "Device settings' \"" + key + "\" list must contain only dictionaries")
                    
                        self.scheduling.append(DeviceSchedule(sched, newScheduling=True))

                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")

    def to_dict(self):
        result = {}
        for key in self.settingsKeys:
            result[key] = getattr(self, key)

        return result

    def save2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise web_exception(400, "Device not found in DB")
            
            for sched in self.scheduling:
                sched.save2DB(DBPath, self.deviceID)

            update_entry_inDB(DBPath, "DeviceSettings", self.to_dict())

        except web_exception as e:
            raise web_exception(400, "An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(500, "An error occurred while saving device settings for device with ID \"" + self.deviceID + "\" to the DB: " + str(e))
        
    def updateDB(self, DBPath):
        self.save2DB(DBPath)

    def set2DB(self, DBPath):
        self.save2DB(DBPath)

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "DeviceSettings", "deviceID", params["deviceID"])):
                raise web_exception(400, "Settings for this device not found in DB")

            delete_entry_fromDB(DBPath, "DeviceSettings", params["deviceID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting device settings for device with ID \"" + params["deviceID"] + "\" from the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(500, "An error occurred while deleting device settings for device with ID \"" + params["deviceID"] + "\" from the DB: " + str(e))
        
    def cleanDB(DBPath):
        query = "SELECT * FROM DeviceSettings"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Devices", "deviceID", entry["deviceID"])):
                    DeviceSettings.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})
        except web_exception as e:
            raise web_exception(400, "An error occurred while cleaning device settings table: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while cleaning device settings table: " + str(e))
        
    
    def DB_to_dict(DBPath, device, verbose = True):
        try:
            deviceID = device["deviceID"]

            if(verbose):
                query = "SELECT * FROM DeviceSettings WHERE deviceID = \"" + deviceID + "\""
                devSettings = DBQuery_to_dict(DBPath, query)[0]
                devSettings["scheduling"] = DeviceSchedule.DB_to_dict(DBPath, deviceID)

            return devSettings
        except web_exception as e:
            raise web_exception(400, "An error occurred while retrieving device settings for device with ID \"" + deviceID + "\" from the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(500, "An error occurred while retrieving device settings for device with ID \"" + deviceID + "\" from the DB: " + str(e))






