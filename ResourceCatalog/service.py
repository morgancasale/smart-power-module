from utility import *
from user import *
from house import *
from devCluster import *

class Service:
    def __init__(self, serviceData, newService = False):
        self.serviceKeys = ["serviceID", "serviceName"]
        self.connTables = ["ServiceHouse_conn", "ServiceUser_conn", "ServiceCluster_conn", "ServiceRes_conn", "ServiceEndP_conn"]

        if(newService) : self.checkKeys(serviceData)
        self.checkSaveValues(serviceData)

        self.serviceData = serviceData

        if(newService):
            self.Online = True
            self.lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def checkKeys(self, serviceData):
        if(not all(key in serviceData.keys() for key in self.serviceKeys)):
            raise web_exception(400, "Missing one or more keys")

    def checkSaveValues(self, serviceData):
        for key in serviceData.keys():
            match key:
                case ("serviceID" | "serviceName"):
                    if(not isinstance(serviceData[key], str)):
                        raise web_exception(400, "Service's \"" + key + "\" parameter must be a string")
                    match key:
                        case "serviceID":
                            self.serviceID = serviceData["serviceID"]
                        case "serviceName":
                            self.name = serviceData["serviceName"]
                case ("houseID" | "userID" | "clusterID" | "resourceID" | "endPointID"):
                    if(not all(isinstance(entryID, str) for entryID in serviceData[key])):
                        raise web_exception(400, "Service's \"" + key + "\" parameter must be a list of strings")
                    match key:
                        case "houseID":
                            self.houseID = serviceData["houseID"]
                        case "userID":
                            self.userID = serviceData["userID"]
                        case "clusterID":
                            self.clusterID = serviceData["clusterID"]
                        case "resourceID":
                            self.resourceID = serviceData["resourceID"]
                        case "endPointID":
                            self.endPointID = serviceData["endPointID"]
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        result = {}

        for key in self.serviceKeys():
            result[key] = self.serviceData[key]
        
        result["Online"] = self.Online
        result["lastUpdate"] = self.lastUpdate

        return result

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Services", "serviceID", self.serviceID)):
                raise web_exception(400, "An service with ID \"" + self.serviceID + "\" already exists in the database")
            
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            if("houseID" in self.serviceData.keys()):
                for houseID in self.houseID:
                    if(not check_presence_inDB(DBPath, "Houses", "houseID", houseID)):
                        raise web_exception(400, "A house with ID \"" + houseID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[0], {"serviceID": self.serviceID, "houseID": houseID, "lastUpdate": self.lastUpdate})

            if("userID" in self.serviceData.keys()):
                for userID in self.userID:
                    if(not check_presence_inDB(DBPath, "Users", "userID", userID)):
                        raise web_exception(400, "An user with ID \"" + userID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[1], {"serviceID": self.serviceID, "userID": userID, "lastUpdate": self.lastUpdate})
            
            if("clusterID" in self.serviceData.keys()):
                for clusterID in self.clusterID:
                    if(not check_presence_inDB(DBPath, "Clusters", "clusterID", clusterID)):
                        raise web_exception(400, "A cluster with ID \"" + clusterID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[2], {"serviceID": self.serviceID, "clusterID": clusterID, "lastUpdate": self.lastUpdate})

            if("deviceID" in self.serviceData.keys()):
                for deviceID in self.deviceID:
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", deviceID)):
                        raise web_exception(400, "A device with ID \"" + deviceID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[3], {"serviceID": self.serviceID, "deviceID": deviceID, "lastUpdate": self.lastUpdate})

            if("resourceID" in self.serviceData.keys()):
                for resourceID in self.resourceID:
                    if(not check_presence_inDB(DBPath, "Resources", "resourceID", resourceID)):
                        raise web_exception(400, "A resource with ID \"" + resourceID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[4], {"serviceID": self.serviceID, "resourceID": resourceID, "Online": self.Online, "lastUpdate": self.lastUpdate})
            
            if("endPointID" in self.serviceData.keys()):
                for endPointID in self.endPointID:
                    if(not check_presence_inDB(DBPath, "EndPoints", "endPointID", endPointID)):
                        raise web_exception(400, "An endpoint with ID \"" + endPointID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[5], {"serviceID": self.serviceID, "endPointID": endPointID, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "Services", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving service with ID \"" + self.serviceID + "\" to the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while saving service with ID \"" + self.serviceID + "\" to the DB:\n\t" + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "Services", "serviceID", self.serviceID)):
                raise web_exception(400, "An service with ID \"" + self.serviceID + "\" does not exist in the database")
            
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            update_entry_inDB(DBPath, "Services", "serviceID", self.to_dict())

            if(self.serviceData["houseID"] != None):
                data = {"table" : self.connTables[0], "refID" : "serviceID", "connID" : "houseID", "refValue" : self.serviceID, "connValues" : self.houseID}
                updateConnTable(DBPath, data, self.Online)
            
            if(self.serviceData["userID"] != None):
                data = {"table" : self.connTables[1], "refID" : "serviceID", "connID" : "userID", "refValue" : self.serviceID, "connValues" : self.userID}
                updateConnTable(DBPath, data, self.Online)

            if(self.serviceData["clusterID"] != None):
                data = {"table" : self.connTables[2], "refID" : "serviceID", "connID" : "clusterID", "refValue" : self.serviceID, "connValues" : self.clusterID}
                updateConnTable(DBPath, data, self.Online)
            
            if(self.serviceData["resourceID"] != None):
                data = {"table" : self.connTables[2], "refID" : "serviceID", "connID" : "resourceID", "refValue" : self.serviceID, "connValues" : self.resourceID}
                updateConnTable(DBPath, data, self.Online)

            if(self.serviceData["endPointID"] != None):
                data = {"table" : self.connTables[3], "refID" : "serviceID", "connID" : "endPointID", "refValue" : self.serviceID, "connValues" : self.endPointID}
                updateConnTable(DBPath, data, self.Online)
                
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating service with ID \"" + self.serviceID + "\" in the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating service with ID \"" + self.serviceID + "\" in the DB:\n\t" + str(e))

    def deleteFromDB(DBPath, params):
        try:
            connTables = ["ServiceHouse_conn", "ServiceUser_conn", "ServiceCluster_conn", "ServiceRes_conn", "ServiceEndP_conn"]
            if(not check_presence_inDB(DBPath, "Services", "serviceID", params["serviceID"])):
                raise web_exception(400, "An service with ID \"" + params["serviceID"] + "\" does not exist in the database")

            for connTable in connTables:
                delete_entry_fromDB(DBPath, connTable, "serviceID", params["serviceID"])
            Device.cleanDB(DBPath)

            delete_entry_fromDB(DBPath, "Services", "serviceID", params["serviceID"])
        except web_exception as e:
            raise web_exception(400, "An error occurred while deleting service with ID \"" + params["serviceID"] + "\" from the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while deleting service with ID \"" + params["serviceID"] + "\" from the DB:\n\t" + str(e))
        
        return True

    def set2DB(self, DBPath):
        try:
            self.Online = True
            if(not check_presence_inDB(DBPath, "Services", "serviceID", self.serviceID)):
                self.save2DB(DBPath)
            else:
                self.updateDB(DBPath)
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving service with ID \"" + self.serviceID + "\" to the DB:\n\t" + str(e.message))
        except Exception as e:
            raise web_exception(400, "An error occurred while saving service with ID \"" + self.serviceID + "\" to the DB:\n\t" + str(e))

    def DB_to_dict(DBPath, service):
        try:
            connTables = ["ServiceHouse_conn", "ServiceUser_conn", "ServiceCluster_conn", "ServiceRes_conn", "ServiceEndP_conn"]
            tablesNames = ["Houses", "Users", "DevClusters", "Devices", "Resources", "EndPoints"]
            varsIDs = ["houseID", "userID", "clusterID", "deviceID", "resourceID", "endPointID"]

            serviceID = service["serviceID"]
            serviceData = {"serviceID": serviceID, "serviceName": service["serviceName"]}

            for i in range(len(connTables)):
                if(check_presence_inDB(DBPath, connTables[i], "serviceID", serviceID)):
                    query = "SELECT * FROM " + connTables[i] + " WHERE serviceID = \"" + serviceID + "\""
                    service_entry_conns = DBQuery_to_dict(DBPath, query)
                    
                    entryIDs = "(\"" + "\", \"".join([service_entry_conn[varsIDs[i]] for service_entry_conn in service_entry_conns]) + "\")"
                    query = "SELECT * FROM " + tablesNames[i] + " WHERE " + varsIDs[i] + " in " + entryIDs
                    results = DBQuery_to_dict(DBPath, query)

                    for result in results:
                        match i:
                            case 0:
                                serviceData["Houses"].append(House.DB_to_dict(DBPath, result, verbose = False))
                            case 1:
                                serviceData["Users"].append(User.DB_to_dict(DBPath, result, verbose = False))
                            case 2: 
                                serviceData["Clusters"].append(DevCluster.DB_to_dict(DBPath, result, verbose = False))
                            case 3:
                                serviceData["Devices"].append(Device.DB_to_dict(DBPath, result, verbose = False))
                            case 4:
                                serviceData["Resources"].append(Resource.DB_to_dict(DBPath, result, verbose = False))
                            case 5:
                                serviceData["EndPoints"].append(EndPoint.DB_to_dict(DBPath, result, verbose = False))
                            case _:
                                raise web_exception(400, "Non valid case")

            return serviceData
        except web_exception as e:
            raise web_exception(400, "An error occurred while retrieving service with ID \"" + serviceID + "\" from the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while retrieving service with ID \"" + serviceID + "\" from the DB:\n\t" + str(e))

    def setOnlineStatus(entries):
        newServiceIDs = []
        newEndPointIDs = []
        newResourceIDs = []

        for entry in entries:
            newServiceIDs.append(entry.serviceID)
            newEndPointIDs.extend([e.endPointID for e in entry.endPoints])
            newResourceIDs.extend([r.resourceID for r in entry.Resources])

        allServiceIDs = getIDs_fromDB(DBPath, "Services", "serviceID")

        missingServiceIDs = list(set(allServiceIDs) - set(newServiceIDs))

        entry = {"serviceID": missingServiceIDs, "Online": False, "lastUpdate": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

        update_entry_inDB(DBPath, "Services", "serviceID", entry)
        EndPoint.setOnlineStatus(newEndPointIDs)
        Resource.setOnlineStatus(newResourceIDs, "ServiceRes_conn")
    