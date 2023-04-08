from utility import *

class Resource:
    def __init__(self, resourceData, newResource = False):
        self.resourceKeys = ["resourceID", "resourceName", "resourceMode", "resourceType", "resourceUnit"]

        if(newResource) : self.checkKeys(resourceData)
        self.checkSaveValues(resourceData)

        self.resourceData = resourceData

        if(newResource):
            self.Online = self.Ping()
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    def checkKeys(self, resourceData):
        if(not all(key in self.resourceKeys for key in resourceData.keys())):
            raise HTTPError(status=400, message="Missing one or more keys")

    def checkSaveValues(self, resourceData):
        for key in resourceData.keys():
            match key:
                case ("resourceID" | "resourceName" | "resourceMode" | "resourceType" | "resourceUnit"):
                    if(not isinstance(resourceData[key], str)):
                        raise HTTPError(status=400, message="Resource's \"" + key + "\" value must be a string")
                    match key:
                        case "resourceID":
                            self.resourceID = resourceData["resourceID"]
                        case "resourceName":
                            self.resourceName = resourceData["resourceName"]
                        case "resourceMode":
                            if(not("read" in resourceData[key] or "write" in resourceData[key])):
                                raise HTTPError(status=400, message="\"resourceMode\" value must be \"read\" or \"write\"")
                            self.resourceMode = resourceData["resourceMode"]
                        case "resourceType":
                            if(not("int" in resourceData[key] or "float" in resourceData[key] or "string" in resourceData[key])):
                                raise HTTPError(status=400, message="\"resourceType\" value must be \"int\", \"float\" or \"string\"")
                            self.resourceType = resourceData["resourceType"]
                        case "resourceUnit":
                            self.resourceUnit = resourceData["resourceUnit"]
                case _:
                    raise HTTPError(status=400, message="Unexpected key \"" + key + "\"")

    def to_dict(self):
        result = {}

        for key in self.resourceData.keys():
            if(key in self.resourceKeys): #TODO forse inutile
                result[key] = self.resourceData[key]

        return result

    def save2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Resources", "resourceID", self.resourceID)):
                save_entry2DB(DBPath, "Resources", self.to_dict())
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving resource with ID \"" + self.resourceID + "\" to the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while saving resource with ID \"" + self.resourceID + "\" to the DB:\n\t" + str(e))
    
    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Resources", "resourceID", self.resourceID)):
                raise HTTPError(status=400, message="Resource with ID \"" + self.resourceID + "\" not found in the DB")

            self.Online = self.Ping()
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            update_entry_inDB(DBPath, "Resources", "resourceID", self.to_dict())

            entry = {
                "resourceID": self.resourceID, "Online": self.Online, "lastUpdate": self.lastUpdate
            }
            update_entry_inDB(DBPath, "DeviceResource_conn", "resourceID", entry)
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while updating resource with ID \"" + self.resourceID + "\" to the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while updating resource with ID \"" + self.resourceID + "\" to the DB:\n\t" + str(e))

    def DB_to_dict(DBPath, resource, requestEntry):
        try:
            query = "SELECT * FROM Resources WHERE resourceID = \"" + resource["resourceID"] + "\""
            data = DBQuery_to_dict(DBPath, query)[0]

            if("deviceID" in requestEntry.keys()):
                query = "SELECT * FROM DeviceResource_conn WHERE (deviceID, resourceID) = (\"" + requestEntry["deviceID"] + "\", \"" + resource["resourceID"] + "\")"
                result = DBQuery_to_dict(DBPath, query)[0]

                if(result == None):
                    raise HTTPError(status=400, message="Device with ID \"" + requestEntry["deviceID"] + "\" doesn't use resource with ID \"" + resource["resourceID"] + "\"")
                data["Online"] = bool(result["Online"])
                data["lastUpdate"] = result["lastUpdate"]

            return data
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while retrieving resource with ID \"" + resource["resourceID"] + "\" from the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while retrieving resource with ID \"" + resource["resourceID"] + "\" from the DB:\n\t" + str(e))

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        try:
            connTables = ["DeviceResource_conn"]

            query = "SELECT * FROM Resources"
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inConnectionTables(DBPath, connTables, "resourceID", entry["resourceID"])):
                    delete_entry_fromDB(DBPath, "Resources", "resourceID", entry["resourceID"])
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while cleaning the DB from resources:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while cleaning the DB from resources:\n\t" + str(e))
    
    def deleteFromDB(DBPath, entry):
        try:
            if(not check_presence_inDB(DBPath, "Resources", "resourceID", entry["resourceID"])):
                raise HTTPError(status=400, message="Resource with ID \"" + entry["resourceID"] + "\" not found in the DB")

            delete_entry_fromDB(DBPath, "DeviceResource_conn", "resourceID", entry["resourceID"])
            delete_entry_fromDB(DBPath, "Resources", "resourceID", entry["resourceID"])
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while deleting resource with ID \"" + entry["resourceID"] + "\" from the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while deleting resource with ID \"" + entry["resourceID"] + "\" from the DB:\n\t" + str(e))

        return True

    def set2DB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Resources", "resourceID", self.resourceID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving resource with ID \"" + self.resourceID + "\" to the DB:\n\t" + str(e._message))
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while saving device with ID \"" + self.resourceID + "\" to the DB:\n\t" + str(e))

    def setOnlineStatus(newResIDs, connTable):
        allResIDs = getIDs_fromDB(DBPath, connTable, "resourceID")
        missingResIDs = list(set(allResIDs) - set(newResIDs))

        entry = {"resourceID": missingResIDs, "Online": False, "lastUpdate": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

        update_entry_inDB(DBPath, connTable, "resourceID", entry)

    def Ping(self):
        #TODO check devices that serve this resource, ping them and return True if at least one is online
        return True
        