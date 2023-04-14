from utility import *
import time
class DeviceSchedule:
    def __init__(self, schedulingData, newSchedule = False):
        self.schedulingKeys = ["deviceID", "socketID", "mode", "startSchedule", "enableEndSchedule", "endSchedule", "repeat"]

        self.enableEndSchedule = False
        self.endSchedule = None
        self.repeat = 0


        if(newSchedule) : self.checkKeys(schedulingData)
        self.checkSaveValues(schedulingData)

    def checkKeys(self, schedulingData):
        if(not all(key in self.schedulingKeys for key in schedulingData.keys())):
            raise HTTPError(status=400, message="Missing one or more keys")
        
    def checkSaveValues(self, schedulingData):
        for key in schedulingData.keys():
            match key:
                case ("deviceID" | "mode"):
                    if(not isinstance(schedulingData[key], str)):
                        raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be a string")
                    match key:
                        case "deviceID": self.deviceID = schedulingData["deviceID"]
                        case "socketID": self.socketID = schedulingData["socketID"]
                        case "mode":
                            if(not schedulingData["mode"] in ["ON", "OFF"]):
                                raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be \"ON\" or \"OFF\"") 
                            self.mode = schedulingData["mode"]

                case ("socketID" | "repeat"):
                    if(not isinstance(schedulingData[key], int) or schedulingData[key] < 0):
                        raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be a positive integer")
                    match key:
                        case "socketID": 
                            if(schedulingData["socketID"] not in [0, 1, 2]):
                                raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be 0, 1 or 2")
                            self.socketID = schedulingData["socketID"]
                        case "repeat": 
                            self.repeat = schedulingData["repeat"]

                case "enableEndSchedule":
                    if(not isinstance(schedulingData[key], bool)):
                        raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be a boolean")
                    self.enableEndSchedule = schedulingData["enableEndSchedule"]
                
                case ("startSchedule"):
                    if(not istimeinstance(schedulingData[key])):
                        raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be feasible timestamp")
                    
                    if(len(schedulingData[key].split("/")[0])<4):
                        timestamp = datetime.strptime(schedulingData[key], "%d-%m-%Y %H:%M")
                    else:
                        timestamp = datetime.strptime(schedulingData[key], "%Y-%m-%d %H:%M")
                    timestamp = time.mktime(timestamp.timetuple())
                    self.startSchedule = timestamp

                case "endSchedule":
                    if(self.enableEndSchedule):
                        if(not istimeinstance(schedulingData[key])):
                            raise HTTPError(status=400, message="Scheduling's \"" + key + "\" value must be feasible timestamp")
                        
                        if(len(schedulingData[key].split("/")[0])<4):
                            timestamp = datetime.strptime(schedulingData[key], "%d/%m/%Y %H:%M")
                        else:
                            timestamp = datetime.strptime(schedulingData[key], "%Y/%m/%d %H:%M")
                        timestamp = time.mktime(timestamp.timetuple())
                        self.endSchedule = timestamp
                    
                case _:
                    raise HTTPError(status=400, message="Unexpected key \"" + key + "\"")
                
    def to_dict(self):
        result = {}
        for key in self.schedulingKeys:
            if(getattr(self, key)!=None) : result[key] = getattr(self, key)
            
        return result
    
    def save2DB(self, DBPath):
        try: 
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise HTTPError(status=400, message="Device with ID \"" + self.deviceID + "\" does not exist")
            
            dictData = self.to_dict()
            if(not check_presence_inDB(DBPath, "DeviceScheduling", list(dictData.keys()), list(dictData.values()))): # Check if scheduling already exists
                save_entry2DB(DBPath, "DeviceScheduling", dictData)

        except HTTPError as e:
            raise HTTPError(status=400, message="An error occured while saving device settings to DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occured while saving device settings to DB:\n\t" + str(e))
        
    def update2DB(self, DBPath):
        self.save2DB(DBPath)
    
    def set2DB(self, DBPath):
        self.save2DB(DBPath)

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "DeviceScheduling", list(params.keys()), list(params.values()))): # Check if scheduling already exists
                raise HTTPError(status=400, message="Scheduling does not exist")
            delete_entry_fromDB(DBPath, "DeviceScheduling", list(params.keys()), list(params.values()))
        
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occured while deleting device settings from DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occured while deleting device settings from DB:\n\t" + str(e))
        
        return True   

    def cleanDB(DBPath):
        query = "SELECT * FROM DeviceScheduling"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Devices", "deviceID", entry["deviceID"])):
                    DeviceSchedule.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})

        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while cleaning the DB from devices:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while cleaning the DB from devices:\n\t" + str(e))
    
    def DB_to_dict(DBPath, deviceID):
        query = "SELECT * FROM DeviceScheduling WHERE deviceID = '" + deviceID + "'"
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
            raise HTTPError(status=400, message="An error occurred while getting device scheduling from DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while getting device scheduling from DB:\n\t" + str(e))


        