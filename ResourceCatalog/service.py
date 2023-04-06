from utility import *
from user import *
from house import *
from device import *

class Service:
    def __init__(self, serviceData, newService = False):
        self.serviceKeys = ["serviceID", "serviceName"]
        self.connTables = ["ServiceHouse_conn", "ServiceUser_conn", "ServiceDevice_conn", "ServiceRes_conn", "ServiceEndP_conn"]

        self.endPoints = []

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
                case ("houseID" | "userID" | "deviceID" | "resourceID"):
                    if(not all(isinstance(entryID, str) for entryID in serviceData[key])):
                        raise web_exception(400, "Service's \"" + key + "\" parameter must be a list of strings")
                    match key:
                        case "houseID":
                            self.houseID = serviceData["houseID"]
                        case "userID":
                            self.userID = serviceData["userID"]
                        case "deviceID":
                            self.deviceID = serviceData["deviceID"]
                        case "resourceID":
                            self.resourceID = serviceData["resourceID"]
                case "endPoints":
                    for endPointData in serviceData["endPoints"]:
                        try:
                            self.endPoints.append(EndPoint(endPointData))
                        except web_exception as e:
                            raise web_exception(e.code, "Service's endPoints with ID " + endPointData["endPointID"] + " is not valid:\n\t" + e.message)
        
                case _:
                    raise web_exception(400, "Unexpected key \"" + key + "\"")
        
        self.checkPresenceOfConnectedinDB(DBPath, serviceData)
        

    def to_dict(self):
        result = {}

        for key in self.serviceKeys:
            result[key] = self.serviceData[key]
        
        result["Online"] = self.Online
        result["lastUpdate"] = self.lastUpdate

        return result
    
    def checkPresenceOfConnectedinDB(self, DBPath, serviceData):
        r"""
        Checks if the IDs of the connected elements are present in the DB
        """

        connectedIDs = ["houseID", "userID", "deviceID", "resourceID"]
        tables = ["Houses", "Users", "Devices", "Resources"]
        for table, connectedID in zip(tables,connectedIDs):
            if(connectedID in serviceData.keys()):
                for ID in serviceData[connectedID]:
                    if(not check_presence_inDB(DBPath, table, connectedID, ID)):
                        raise web_exception(400, "A " + table[:-1] + " with ID \"" + ID + "\" does not exist in the database")

    def save2DB(self, DBPath):
        endPointIDs = []

        try:
            if(check_presence_inDB(DBPath, "Services", "serviceID", self.serviceID)):
                raise web_exception(400, "An service with ID \"" + self.serviceID + "\" already exists in the database")
            
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            for endPoint in self.endPoints:
                try:
                    endPoint.set2DB(DBPath)
                except web_exception as e:
                    msg = "An error occurred while saving service's endPoints with ID " + endPoint.endPointID + " is not valid:\n\t" + e.message
                    raise web_exception(e.code, msg)
                except Exception as e:
                    msg = "An error occurred while saving service's endPoints with ID " + endPoint.endPointID + " is not valid:\n\t" + str(e)
                    raise web_exception(500, msg)
                
                endPointIDs.append(endPoint.endPointID)

            if("houseID" in self.serviceData.keys()):
                for houseID in self.houseID:
                    save_entry2DB(DBPath, self.connTables[0], {"serviceID": self.serviceID, "houseID": houseID, "lastUpdate": self.lastUpdate})

            if("userID" in self.serviceData.keys()):
                for userID in self.userID:
                    save_entry2DB(DBPath, self.connTables[1], {"serviceID": self.serviceID, "userID": userID, "lastUpdate": self.lastUpdate})
            
            if("deviceID" in self.serviceData.keys()):
                for deviceID in self.deviceID:
                    save_entry2DB(DBPath, self.connTables[2], {"serviceID": self.serviceID, "deviceID": deviceID, "lastUpdate": self.lastUpdate})

            if("resourceID" in self.serviceData.keys()):
                for resourceID in self.resourceID:
                    save_entry2DB(DBPath, self.connTables[3], {"serviceID": self.serviceID, "resourceID": resourceID, "Online": self.Online, "lastUpdate": self.lastUpdate})
            
            if(len(endPointIDs)>0):
                for endPointID in endPointIDs:
                    save_entry2DB(DBPath, self.connTables[4], {"serviceID": self.serviceID, "endPointID": endPointID, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "Services", self.to_dict())
        except web_exception as e:
            raise web_exception(400, "An error occurred while saving service with ID \"" + self.serviceID + "\" to the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while saving service with ID \"" + self.serviceID + "\" to the DB:\n\t" + str(e))

    def updateDB(self, DBPath):
        endPointIDs = []

        try:
            if(not check_presence_inDB(DBPath, "Services", "serviceID", self.serviceID)):
                raise web_exception(400, "An service with ID \"" + self.serviceID + "\" does not exist in the database")
            
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            for endPoint in self.endPoints:
                try:
                    endPoint.set2DB(DBPath)
                except web_exception as e:
                    msg = "An error occurred while updating service's endPoints with ID " + endPoint.endPointID +":\n\t" + e.message
                    raise web_exception(e.code, msg)
                except Exception as e:
                    msg = "An error occurred while saving service's endPoints with ID " + endPoint.endPointID + ":\n\t" + str(e)
                    raise web_exception(500, msg)
                
                endPointIDs.append(endPoint.endPointID)
            
            update_entry_inDB(DBPath, "Services", "serviceID", self.to_dict())
            

            if("houseID" in self.serviceData.keys()):
                data = {"table" : self.connTables[0], "refID" : "serviceID", "connID" : "houseID", "refValue" : self.serviceID, "connValues" : self.houseID}
                updateConnTable(DBPath, data)
            
            if("userID" in self.serviceData.keys()):
                data = {"table" : self.connTables[1], "refID" : "serviceID", "connID" : "userID", "refValue" : self.serviceID, "connValues" : self.userID}
                updateConnTable(DBPath, data)

            if("deviceID" in self.serviceData.keys()):
                data = {"table" : self.connTables[2], "refID" : "serviceID", "connID" : "deviceID", "refValue" : self.serviceID, "connValues" : self.deviceID}
                updateConnTable(DBPath, data)
            
            if("resourceID" in self.serviceData.keys()):
                data = {"table" : self.connTables[3], "refID" : "serviceID", "connID" : "resourceID", "refValue" : self.serviceID, "connValues" : self.resourceID}
                updateConnTable(DBPath, data, self.Online)

            if(len(endPointIDs)>0):
                data = {"table" : self.connTables[4], "refID" : "serviceID", "connID" : "endPointID", "refValue" : self.serviceID, "connValues" : endPointIDs}
                updateConnTable(DBPath, data)
                
        except web_exception as e:
            raise web_exception(400, "An error occurred while updating service with ID \"" + self.serviceID + "\" in the DB:\n\t" + e.message)
        except Exception as e:
            raise web_exception(400, "An error occurred while updating service with ID \"" + self.serviceID + "\" in the DB:\n\t" + str(e))

    def deleteFromDB(DBPath, params):
        try:
            connTables = ["ServiceHouse_conn", "ServiceUser_conn", "ServiceDevice_conn", "ServiceRes_conn", "ServiceEndP_conn"]
            if(not check_presence_inDB(DBPath, "Services", "serviceID", params["serviceID"])):
                raise web_exception(400, "An service with ID \"" + params["serviceID"] + "\" does not exist in the database")

            for connTable in connTables:
                delete_entry_fromDB(DBPath, connTable, "serviceID", params["serviceID"])

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
            connTables = ["ServiceHouse_conn", "ServiceUser_conn", "ServiceDevice_conn", "ServiceRes_conn", "ServiceEndP_conn"]
            tablesNames = ["Houses", "Users", "DevDevices", "Devices", "Resources", "EndPoints"]
            varsIDs = ["houseID", "userID", "deviceID", "deviceID", "resourceID", "endPointID"]

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
                                serviceData["Devices"].append(Device.DB_to_dict(DBPath, result, verbose = False))
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
    