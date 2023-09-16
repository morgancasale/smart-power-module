import json
import pandas as pd
import sqlite3 as sq

import os
import sys
import socket

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from house import *
from houseSettings import *

from socketClass import *

from devSettings import *
from appliance import *

from service import *

from microserviceBase.serviceBase import *
from cherrypy import HTTPError

class ResourceCatalog:
    def __init__(self, DBPath):
        if(not os.path.isfile(DBPath)):
            raise Server_Error_Handler.InternalServerError(message="The DB file does not exist")
        self.DBPath = DBPath

        configFile_loc = "serviceConfig.json"
        if(not IN_DOCKER): configFile_loc = "ResourceCatalog/" + configFile_loc

        self.server = ServiceBase(
            configFile_loc,
            GET=self.handleGetRequest, POST=self.handlePostRequest, 
            PUT=self.handlePutRequest, PATCH=self.handlePatchRequest,
            DELETE=self.handleDeleteRequest
        )
        self.server.start()
        
    
    def handleGetRequest(self, *uri, **params):
        cmd = uri[1]
        if(not isinstance(params, list)) : params = [params]
        try:
            match cmd:
                case "getInfo":
                    for entry in params:
                        return self.extractByKey(entry)
                    
                case "checkPresence":
                    for entry in params:
                        return self.checkPresence(entry)
                    
                case "getNetworkIP":
                    return socket.gethostbyname(socket.gethostname())
                
                case "exit":
                    return self.exit(self.filename)

                case _:
                    raise Server_Error_Handler.NotImplemented(message="The command \"" + cmd + "\" is not valid")
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while handling the GET request:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while handling the GET request:\u0085\u0009" + e._message)
        

    def handlePostRequest(self, *uri):
        cmd = uri[1]
        params = cherrypy.request.json
        if(not isinstance(params, list)) : params = [params]
        try:
            match cmd:            
                case "regHouse":
                    for houseData in params:
                        entry = House(houseData, newHouse = True)
                        entry.save2DB(self.DBPath)
                    return "House registration was successful"

                case "regUser":
                    for userData in params:
                        entry = User(userData, newUser = True)
                        entry.save2DB(self.DBPath)
                    return "User registration was successful"

                case "regDevice":
                    for deviceData in params:
                        entry = Device(deviceData, newDevice = True)

                        entry.save2DB(self.DBPath)
                    return "Device registration was successful"
                
                case "regSocket":
                    for socketData in params:
                        entry = Socket(self.DBPath, socketData, newSocket = True)

                        entry.save2DB(self.DBPath)
                    return "Socket registration was successful"
                
                case "regEndPoint":
                    for endPointData in params:
                        entry = EndPoint(endPointData, newEndPoint = True)
                        entry.save2DB(self.DBPath)
                    return "End Point registration was successful"
                
                case "regService":
                    for serviceData in params:
                        entry = Service(self.DBPath, serviceData, newService = True)
                        entry.save2DB(self.DBPath)
                    return "Service registration was successful"
                
                case "regAppliancesInfo":
                    for applianceData in params:
                        entry = Appliance(applianceData, newAppliance = True)
                        entry.save2DB(self.DBPath)
                    return "Appliance registration was successful"
                
                    
                case "exit":
                    exit()

                case _:
                    raise Server_Error_Handler.NotImplemented(message="The command \"" + cmd + "\" is not valid")
        except HTTPError as e:
            raise HTTPError(status=e.status, message ="An error occurred while handling the POST request:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while handling the POST request:\u0085\u0009" + str(e))

    def handlePutRequest(self, *uri):
        cmd = uri[1]
        params = cherrypy.request.json
        if(not isinstance(params, list)) : params = [params]
        try:
            match cmd:
                case "setHouse":
                    for houseData in params:
                        entry = House(houseData)
                        entry.set2DB(self.DBPath)
                    return "House update was successful"
                
                case "setHouseSettings":
                    for houseSettingsData in params:
                        entry = HouseSettings(houseSettingsData)
                        entry.set2DB(self.DBPath)
                    return "House settings update was successful"

                case "setUser":
                    for userData in params:
                        entry = User(userData)
                        entry.set2DB(self.DBPath)
                    return "User update was successful"

                case "setDevice":
                    entries = []

                    for deviceData in params:
                        entry = Device(deviceData, newDevice = True)
                        entries.append(entry)
                        entry.set2DB(self.DBPath)
                    
                    #Device.setOnlineStatus(entries)
                    return "Device update was successful"
                
                case "setSocket":
                    for socketData in params:
                        entry = Socket(self.DBPath, socketData)
                        entry.set2DB(self.DBPath)
                    return "Socket update was successful"
                
                case "setService":
                    for serviceData in params:
                        entry = Service(self.DBPath, serviceData)
                        entry.set2DB(self.DBPath)
                    return "Service update was successful"

                case "setResource":
                    for resourceData in params:
                        entry = Resource(resourceData)
                        entry.set2DB(self.DBPath)
                    return "Resource update was successful"

                case "setEndPoint":
                    for endPointData in params:
                        entry = EndPoint(endPointData)
                        entry.set2DB(self.DBPath)
                    return "EndPoint update was successful"

                case "setService":
                    entries = []

                    for serviceData in params:
                        entry = Service(self.DBPath, serviceData, newService = True)
                        entries.append(entry)
                        entry.set2DB(self.DBPath)
                    
                    #Service.setOnlineStatus(entries)
                    return "Device update was successful"
                
                case "setDeviceSettings":
                    for DeviceSettingsData in params:
                        entry = DeviceSettings(DeviceSettingsData, newSettings = True)
                        entry.set2DB(self.DBPath)
                    return "Device settings update was successful"
                
                case "setDeviceSchedule":
                    for deviceScheduleData in params:
                        entry = DeviceSchedule(deviceScheduleData, newSchedule = True)
                        entry.set2DB(self.DBPath)
                    return "Device schedule update was successful"
                
                case "setAppliancesInfo":
                    for applianceData in params:
                        entry = Appliance(applianceData, newAppliance = True)
                        entry.set2DB(self.DBPath)
                    return "Appliance update was successful"
                
                case "setOnlineStatus":
                    results = []
                    for entry in params:
                        results.append(setOnlineStatus(self.DBPath, entry))
                    return results
                
                case "exit":
                    exit()

                case _:
                    raise Server_Error_Handler.NotImplemented(message="The command \"" + cmd + "\" is not valid")
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while handling the PUT request:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while handling the PUT request:\u0085\u0009" + str(e))

    def handlePatchRequest(self, *uri):
        cmd = uri[1]
        params = cherrypy.request.json
        if(not isinstance(params, list)) : params = [params]
        try:
            match cmd:                
                case "updateHouse":
                    for houseData in params:
                        entry = House(houseData)
                        entry.updateDB(self.DBPath)
                    return "House update was successful"

                case "updateUser":
                    for userData in params:
                        entry = User(userData)
                        entry.updateDB(self.DBPath)
                    return "User update was successful"

                case "updateDevice":
                    for deviceData in params:
                        entry = Device(deviceData)
                        entry.updateDB(self.DBPath)
                    return "Device update was successful"
                
                case "updateSocket":
                    for socketData in params:
                        entry = Socket(self.DBPath, socketData)
                        entry.updateDB(self.DBPath)
                    return "Socket update was successful"

                case "updateService":
                    for serviceData in params:
                        entry = Service(self.DBPath, serviceData)
                        entry.updateDB(self.DBPath)
                    return "Service update was successful"
                
                case "updateResource":
                    for resourceData in params:
                        entry = Resource(resourceData)
                        entry.updateDB(self.DBPath)
                    return "Resource update was successful"

                case "updateEndPoint":
                    for endPointData in params:
                        entry = EndPoint(endPointData)
                        entry.updateDB(self.DBPath)
                    return "EndPoint update was successful"

                case "updateConnStatus":
                    for connData in params:
                        self.updateConnStatus(connData)
                    return "Connection update was successful"
                
                case "updateOnlineStatus":
                    results = []
                    for entry in params:
                        results.append(updateOnlineStatus(self.DBPath, entry))
                    return ("\n\t").join(results)
                
                case "exit":
                    exit()

                case _:
                    raise Server_Error_Handler.NotImplemented(message="The command \"" + cmd + "\" is not valid")
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while handling the PATCH request:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while handling the PATCH request:\u0085\u0009" + str(e))

    def handleDeleteRequest(self, *uri, **params): #TODO : streamline using the same method for all classes
        cmd = uri[1]
        if(not isinstance(params, list)) : params = [params]
        try:
            match cmd:
                case "delHouse":
                    for entry in params:
                        House.deleteFromDB(self.DBPath, entry)
                    return "House deletion was successful"

                case "delUser":
                    for entry in params:
                        User.deleteFromDB(self.DBPath, entry)
                    return "User deletion was successful"

                case "delDevice":
                    for entry in params:
                        Device.deleteFromDB(self.DBPath, entry)
                    return "Device deletion was successful"
                
                case "delSocket":
                    for entry in params:
                        Socket.deleteFromDB(self.DBPath, entry)
                    return "Socket deletion was successful"

                case "delService":
                    for entry in params:
                        Service.deleteFromDB(self.DBPath, entry)
                    return "Service deletion was successful"

                case "delResource":
                    for entry in params:
                        Resource.deleteFromDB(self.DBPath, entry)
                    return "Resource deletion was successful"

                case "delEndPoint":
                    for entry in params:
                        EndPoint.deleteFromDB(self.DBPath, entry)
                    return "EndPoint deletion was successful"
                
                case "delDevSettings":
                    for entry in params:
                        DeviceSettings.deleteFromDB(self.DBPath, entry)
                    return "Device Settings deletion was successful"
                
                case "delDevSchedule":
                    for entry in params:
                        DeviceSchedule.deleteFromDB(self.DBPath, entry)
                    return "Device Schedule deletion was successful"
                
                case "delAppliancesInfo":
                    for entry in params:
                        Appliance.deleteFromDB(self.DBPath, entry)
                    return "Appliance deletion was successful"

                case "exit":
                    exit()

                case _:
                    raise Server_Error_Handler.NotImplemented(message="The command \"" + cmd + "\" is not valid")
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while handling the DELETE request:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while handling the DELETE request:\u0085\u0009" + str(e))   

    def reconstructJson(self, table, selectedData, requestEntry, verbose = False):
        reconstructedData = []
        try:
            for sel in selectedData:
                match table:
                    case "Houses":
                        reconstructedData.append(House.DB_to_dict(self.DBPath, sel, verbose=verbose))
                    case "HouseSettings":
                        reconstructedData.append(HouseSettings.DB_to_dict(self.DBPath, sel))
                    case "Services":
                        reconstructedData.append(Service.DB_to_dict(self.DBPath, sel, verbose=verbose))
                    case "Users":
                        reconstructedData.append(User.DB_to_dict(self.DBPath, sel, verbose=verbose))
                    case "Devices":
                        reconstructedData.append(Device.DB_to_dict(self.DBPath, sel, verbose=verbose))
                    case "Sockets":
                        reconstructedData.append(Socket.DB_to_dict(self.DBPath, sel))
                    case "Resources":
                        reconstructedData.append(Resource.DB_to_dict(self.DBPath, sel, requestEntry))
                    case "EndPoints":
                        reconstructedData.append(EndPoint.DB_to_dict(self.DBPath, sel))
                    case "DeviceSettings":
                        reconstructedData.append(DeviceSettings.DB_to_dict(self.DBPath, sel))
                    case "DeviceScheduling":
                        reconstructedData.append(DeviceSchedule.DB_to_dict(self.DBPath, sel))
                    case "AppliancesInfo":
                        reconstructedData.append(Appliance.DB_to_dict(self.DBPath, sel))
                    case _:
                        if("_conn" in table):
                            reconstructedData.append(sel)
                        else:
                            raise Server_Error_Handler.NotImplemented(message="Unexpected invalid table")
                    
            return reconstructedData
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while reconstructing data:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while reconstructing data:\u0085\u0009" + str(e))
    
    def checkPresence(self, entry): # check if an entry is present in the DB
        try:
            table = entry["table"]
            keyName = entry["keyName"]
            keyValue = entry["keyValue"]
            
            return json.dumps({"result" : check_presence_inDB(self.DBPath, table, keyName, keyValue)})
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while checking the presence of an entry in the DB:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while checking the presence of an entry in the DB:\u0085\u0009" + str(e))         

    def extractByKey(self, entry):
        try:
            table = entry["table"]
            keyName = entry["keyName"]
            keyValue = entry["keyValue"]
            verbose = False
            if("verbose" in entry.keys()): verbose = (entry["verbose"] == "True")        

            selectedData = None

            if(not isinstance(keyValue, list)) : keyValue = [keyValue]

            if(not isinstance(keyName, str)):
                raise Client_Error_Handler.BadRequest(message="Key name must be a single string") 
            if(not all(isinstance(keyV, str) for keyV in keyValue)):
                raise Client_Error_Handler.BadRequest(message="Key values must be string")       
            if(not isinstance(table, str)):
                raise Client_Error_Handler.BadRequest(message="Table name must be single string")

            if(not isinstance(keyValue, list)) : keyValue = [keyValue]

            try:
                conn = sq.connect(self.DBPath)       
                if(keyValue[0] == "*"):
                    query = "SELECT * FROM " + table
                else:
                    query = "SELECT * FROM " + table + " WHERE " + keyName + " IN (\"" + "\", \"".join(keyValue) + "\")"
                
                selectedData = pd.read_sql_query(query, conn).to_dict(orient="records")
                conn.close()
            except Exception as e:
                raise Server_Error_Handler.InternalServerError(message="An error occured while extracting data from DB:\u0085\u0009" + str(e))

            if len(selectedData) == 0:
                message = "No entry found in table \"" + table
                message += "\" with key " + keyName + " and values " + "[\"" + "\", \"".join(keyValue) + "\"]"
                raise Client_Error_Handler.NotFound(message=message)

            reconstructedData = None
            reconstructedData = ResourceCatalog.reconstructJson(self, table, selectedData, entry, verbose=verbose)
            
            return json.dumps(reconstructedData)
        except HTTPError as e:
            raise HTTPError(status=e.status, message = "An error occurred while extracting data from DB:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while extracting data from DB:\u0085\u0009" + str(e))
        

    def updateConnStatus(self, connData): #TODO check integrity of request
        try:
            if(not check_presence_ofTableInDB(self.DBPath, connData["table"])): 
                raise Client_Error_Handler.NotFound(message="The table \"" + connData["table"] + "\" does not exist")
            
            for keyName in connData["keyName"]:
                if(not check_presence_ofColumnInDB(self.DBPath, connData["table"], keyName)):
                    raise Client_Error_Handler.NotFound(message="The column \"" + keyName + "\" does not exist in the table \"" + connData["table"] + "\"")
            
            for conn in connData["conns"]:               
                if(conn["new_status"]):
                    entry = dict(zip(connData["keyName"], conn["keyValue"]))
                    entry["lastUpdate"] = time.time()
                    if(not check_presence_inDB(self.DBPath, connData["table"], connData["keyName"], conn["keyValue"])):
                        save_entry2DB(DBPath, connData["table"], entry)
                
                else:
                    if(not check_presence_inDB(self.DBPath, connData["table"], connData["keyName"], conn["keyValue"])):
                        message = "The entry (\"" + conn["keyValue"][0] +", " + conn["keyValue"][1]
                        message += "\") does not exist in the table \"" + connData["table"] + "\""
                        Client_Error_Handler.NotFound(message=message)

                    delete_entry_fromDB(self.DBPath, connData["table"], connData["keyName"], conn["keyValue"])

        except HTTPError as e:
            raise HTTPError(status=e.status, message ="An error occurred while updating a connection:\u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while updating a connection:\u0085\u0009" + str(e))        

if __name__ == "__main__":
    DBPath = "db.sqlite"
    if not IN_DOCKER:
        DBPath = "ResourceCatalog/" + DBPath
    resourceCatalog = ResourceCatalog(DBPath)
