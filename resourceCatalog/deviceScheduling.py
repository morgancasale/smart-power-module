import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from utility import *
import time

from microserviceBase.Error_Handler import *
class DeviceSchedule:
    def __init__(self, schedulingData, DBPath, newSchedule = False):
        self.schedulingKeys = ["deviceID", "socketID", "mode", "startSchedule", "enableEndSchedule", "endSchedule", "repeat"]

        self.enableEndSchedule = False
        self.endSchedule = None
        self.repeat = 0


        if(newSchedule) : 
            self.checkKeys(schedulingData)
            self.scheduleID = self.generateID(DBPath)
        self.checkSaveValues(schedulingData)
        
    def checkKeys(self, schedulingData):
        a = set(schedulingData.keys())
        b = set(self.schedulingKeys)
        if(not b.issubset(a)):
            raise Client_Error_Handler.BadRequest(message="Missing one or more keys")
        
    def checkSaveValues(self, schedulingData):
        for key in schedulingData.keys():
            match key:
                case ("deviceID" | "scheduleID" | "mode"):
                    if(not isinstance(schedulingData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be string")
                    match key:
                        case "deviceID": self.deviceID = schedulingData["deviceID"]
                        case "scheduleID": self.socketID = schedulingData["scheduleID"]
                        case "mode":
                            if(not schedulingData["mode"] in ["ON", "OFF"]):
                                raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be \"ON\" or \"OFF\"")
                            self.mode = schedulingData["mode"]

                case ("socketID" | "repeat"):
                    if(not isinstance(schedulingData[key], int) or schedulingData[key] < 0):
                        raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be a positive number")
                    match key:
                        case "socketID": 
                            if(schedulingData["socketID"] not in [0, 1, 2]):
                                raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be 0, 1 or 2")
                            self.socketID = schedulingData["socketID"]
                        case "repeat": 
                            self.repeat = schedulingData["repeat"]

                case "enableEndSchedule":
                    if(not isinstance(schedulingData[key], bool)):
                        raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be boolean")
                    self.enableEndSchedule = schedulingData["enableEndSchedule"]
                
                case ("startSchedule"):
                    if(not istimeinstance(schedulingData[key])):
                        raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be feasible timestamp")
                    
                    if(schedulingData[key].count(":") < 2):
                        schedulingData[key] += ":00"

                    if(len(schedulingData[key].split("/")[0])<4):
                        timestamp = datetime.strptime(schedulingData[key], "%d/%m/%Y %H:%M:%S")
                    else:
                        timestamp = datetime.strptime(schedulingData[key], "%Y/%m/%d %H:%M:%S")
                    timestamp = time.mktime(timestamp.timetuple())
                    self.startSchedule = timestamp

                case "endSchedule":
                    if(self.enableEndSchedule):
                        if(not istimeinstance(schedulingData[key])):
                            raise Client_Error_Handler.BadRequest(message="Scheduling's \"" + key + "\" value must be feasible timestamp")
                        
                        if(schedulingData[key].count(":") < 2):
                            schedulingData[key] += ":00"

                        if(len(schedulingData[key].split("/")[0])<4):
                            timestamp = datetime.strptime(schedulingData[key], "%d/%m/%Y %H:%M:%S")
                        else:
                            timestamp = datetime.strptime(schedulingData[key], "%Y/%m/%d %H:%M:%S")
                        timestamp = time.mktime(timestamp.timetuple())
                        self.endSchedule = timestamp
                    
                case _:
                    raise Client_Error_Handler.BadRequest(message="Unexpected key \"" + key + "\"")
                
    def to_dict(self):
        result = {}
        try:
            for key in self.schedulingKeys:
                if(getattr(self, key)!=None) : result[key] = getattr(self, key)
            
            result["scheduleID"] = self.scheduleID
                
            return result
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occured while converting device settings to dictionary:\u0085\u0009" + str(e)
            )
        
    def generateID(self, DBPath):
        try:
            existence = True
            while(existence):
                newID = "SCH" + randomB64String(4)

                existence = check_presence_inDB(DBPath, "DeviceScheduling", "scheduleID", newID)
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))
        
        return newID
        
    def save2DB(self, DBPath):
        try: 
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID, False)):
                raise HTTPError(status=400, message="Device with ID \"" + self.deviceID + "\" does not exist")
            
            dictData = self.to_dict()
            if(not check_presence_inDB(DBPath, "DeviceScheduling", list(dictData.keys()), list(dictData.values()))): # Check if scheduling already exists
                save_entry2DB(DBPath, "DeviceScheduling", dictData)

        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occured while saving device settings to DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occured while saving device settings to DB:\u0085\u0009" + str(e)
            )
        
    def update2DB(self, DBPath):
        self.save2DB(DBPath)
    
    def set2DB(self, DBPath):
        self.save2DB(DBPath)

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "DeviceScheduling", "scheduleID", params["scheduleID"])): # Check if scheduling already exists
                raise HTTPError(status=400, message="Scheduling does not exist")
            delete_entry_fromDB(DBPath, "DeviceScheduling", "scheduleID", params["scheduleID"])
        
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occured while deleting device settings from DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occured while deleting device settings from DB:\u0085\u0009" + str(e)
            )
        
        return True   

    def cleanDB(DBPath):
        query = "SELECT * FROM DeviceScheduling"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Devices", "deviceID", entry["deviceID"], False)):
                    DeviceSchedule.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})

        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while cleaning the DB from devices:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while cleaning the DB from devices:\u0085\u0009" + str(e)
            )
    
    def DB_to_dict(DBPath, data):
        ID = None
        if(type(data) == dict) : ID = data["deviceID"]
        elif(type(data) == str) : ID = data
        query = "SELECT * FROM DeviceScheduling WHERE deviceID = '" + ID + "'"
        try:
            data = DBQuery_to_dict(DBPath, query)

            if(data != [None]):
                for d in data:
                    if(d["startSchedule"] != None):
                        d["startSchedule"] = datetime.fromtimestamp(d["startSchedule"]).strftime("%d/%m/%Y %H:%M")
                    if(d["endSchedule"] != None):
                        d["endSchedule"] = datetime.fromtimestamp(d["endSchedule"]).strftime("%d/%m/%Y %H:%M")
            else:
                data = None

            return data

        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while getting device scheduling from DB:\u0085\u0009" + str(e._message))
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while getting device scheduling from DB:\u0085\u0009" + str(e)
            )


        