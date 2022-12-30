from utility import *

class Resource:
    def __init__(self, resourceData):
        self.resourceKeys = ["resourceID", "resourceName"]

        self.checkKeys(resourceData)
        self.checkValues(resourceData)

        self.resourceID = resourceData["resourceID"]
        self.resourceName = resourceData["resourceName"]
        self.Online = self.Ping(self.endPoints)
        self.lastUpdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def checkKeys(self, resourceData):
        if(not all(key in self.resourceKeys for key in resourceData.keys())):
            raise web_exception(400, "Missing one or more keys")

    def checkValues(self, resourceData):
        if(resourceData["resourceID"] == None):
            raise web_exception(400, "\"resourceID\" value must be a not null string")
        if(not isinstance(resourceData["resourceID"], str)):
            raise web_exception(400, "\"resourceID\" value must be a string")

        if(resourceData["resourceName"] == None):
            raise web_exception(400, "\"resourceName\" value must be a not null string")
        if(not isinstance(resourceData["resourceName"], str)):
            raise web_exception(400, "\"resourceName\" value must be a string")

    def to_dict(self):
        return {"resourceID": self.resourceID, "resourceName": self.resourceName,
                "lastUpdate": self.lastUpdate, "Online": self.Online}

    def save2DB(self, DBPath):
        try:
            self.Online = self.Ping(self.endPoints)
            if(not check_presence_inDB(DBPath, "Resources", "resourceID", self.resourceID)):
                save_entry2DB(DBPath, "Resources", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving resource with ID \"" + self.resourceID + "\" to the DB: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving resource with ID \"" + self.resourceID + "\" to the DB: " + e)

    def DB_to_dict(DBPath, resource):
        try:
            query = "SELECT * FROM Resources WHERE resourceID = \"" + resource["resourceID"] + "\""
            return DBQuery_to_dict(DBPath, query)[0]
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving resource with ID \"" + resource["resourceID"] + "\" from the DB: " + e)

    def cleanDB(DBPath): #TODO forse c'è un modo più furbo di fare questa funzione usando solo sql
        try:
            connTables = ["DeviceResource_conn"]

            query = "SELECT * FROM Resources"
            data = DBQuery_to_dict(DBPath, query)

            for entry in data:
                if(not check_presence_inConnectionTables(DBPath, connTables, "resourceID", entry["resourceID"])):
                    delete_entry_fromDB(DBPath, "Resources", "resourceID", entry["resourceID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from resources: " + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while cleaning the DB from resources: " + e)

    def Ping(self, endPoints):
        return True
        