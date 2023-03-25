from utility import *
class DeviceSchedule:
    def __init__(self, schedulingData, newSchedule = False):
        self.schedulingKeys = ["deviceID", "socketID", "startSchedule", "enableEndSchedule", "endSchedule", "repeat"]

        if(newSchedule) : self.checkKeys(schedulingData)
        self.checkSaveValues(schedulingData)

    def checkKeys(self, schedulingData):
        if(not all(key in self.schedulingKeys for key in schedulingData.keys())):
            raise web_exception(400, "Missing one or more keys")
        
    def checkSaveValues(self, schedulingData):
        for key in schedulingData.keys():
            match key:
                case ("deviceID" | "socketID"):
                    if(not isinstance(schedulingData[key], str)):
                        raise web_exception(400, "Scheduling's \"" + key + "\" value must be a string")
                    match key:
                        case "deviceID": self.deviceID = schedulingData["deviceID"]
                        case "socketID": self.socketID = schedulingData["socketID"]

                case "enableEndSchedule":
                    if(not isinstance(schedulingData[key], bool)):
                        raise web_exception(400, "Scheduling's \"" + key + "\" value must be a boolean")
                    self.enableEndSchedule = schedulingData["enableEndSchedule"]
                
                case ("startSchedule" | "endSchedule"):
                    if(not istimeinstance(schedulingData[key])):
                        raise web_exception(400, "Scheduling's \"" + key + "\" value must be feasible timestamp")
                    
                    timestamp = datetime.strptime(schedulingData[key], "%d/%m/%Y %H:%M")
                    timestamp = time.mktime(timestamp.timetuple())
                    match key:
                        case "startSchedule": self.startSchedule = timestamp
                        case "endSchedule": self.endSchedule = timestamp
                    
                case "repeat":
                    if(not isinstance(schedulingData[key], int) or schedulingData[key] < 0):
                        raise web_exception(400, "Scheduling's \"" + key + "\" value must be a positive integer")
                    self.repeat = schedulingData["repeat"]
                    
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
                
    def to_dict(self):
        return { "deviceID": self.deviceID, "socketID": self.socketID, "startSchedule": self.startSchedule,
                 "enableEndSchedule": self.enableEndSchedule, "endSchedule": self.endSchedule, "repeat": self.repeat }
    
    def save2DB(self, DBPath):
        try: 
            if(not check_presence_inDB(DBPath, "Devices", "deviceID", self.deviceID)):
                raise web_exception(400, "Device with ID \"" + self.deviceID + "\" does not exist")
            
            if(not check_presence_inDB(DBPath, "DeviceSettings", self.schedulingKeys, self.to_dict().values())): # Check if scheduling already exists
                save_entry2DB(DBPath, "DeviceSettings", self.to_dict())

        except web_exception as e:
            raise web_exception(400, "An error occured while saving device settings to DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occured while saving device settings to DB: " + str(e))
        
    def update2DB(self, DBPath):
        self.save2DB(DBPath)
    
    def set2DB(self, DBPath):
        self.save2DB(DBPath)

    def deleteFromDB(DBPath, params):
        try:
            if(not check_presence_inDB(DBPath, "DeviceSettings", params.keys(), params.values())): # Check if scheduling already exists
                raise web_exception(400, "Scheduling does not exist")
            delete_entry_fromDB(DBPath, "DeviceSettings", params.keys(), params.values())
        
        except web_exception as e:
            raise web_exception(400, "An error occured while deleting device settings from DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occured while deleting device settings from DB: " + str(e))
        
        return True   

    def cleanDB(DBPath):
        query = "SELECT * FROM DeviceSettings"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inDB(DBPath, "Devices", "deviceID", entry["deviceID"])):
                    DeviceSchedule.deleteFromDB(DBPath, {"deviceID": entry["deviceID"]})

        except web_exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from devices: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from devices: " + str(e))
    
    def DB_to_dict(DBPath, deviceID, verbose = True):
        query = "SELECT * FROM DeviceScheduling WHERE deviceID = '" + deviceID + "'"
        try:
            data = DBQuery_to_dict(DBPath, query)

            for d in data:
                if(d["startSchedule"] != None):
                    d["startSchedule"] = datetime.fromtimestamp(d["startSchedule"]).strftime("%d/%m/%Y %H:%M")
                if(d["endSchedule"] != None):
                    d["endSchedule"] = datetime.fromtimestamp(d["endSchedule"]).strftime("%d/%m/%Y %H:%M")

            if(verbose): return data

        except web_exception as e:
            raise web_exception(400, "An error occurred while getting device scheduling from DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while getting device scheduling from DB: " + str(e))


        