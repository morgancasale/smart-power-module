import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from utility import *
from microserviceBase.Error_Handler import *

class Socket:
    def __init__(self, socketData, newSocket = True):
        self.socketKeys = sorted([
            "deviceID", "HAID", "MAC", "masterNode", "RSSI"
        ])
        
        if(newSocket) : self.checkKeys(socketData)
        self.checkSaveValues(socketData)

    def checkKeys(self, socketData):
        if(not sorted(socketData.keys()) == self.socketKeys):
            raise Client_Error_Handler.BadRequest(message="Missing one or more keys")
        
    def checkSaveValues(self, socketData):
        for key in socketData.keys():
            match key:
                case ("deviceID"):
                    if(not isinstance(socketData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="Socket's \"" + key + "\" value must be string")
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", socketData[key])):
                        raise Client_Error_Handler.BadRequest(message="Socket's deviceID not found in DB")
                    self.deviceID = socketData["deviceID"]

                case "HAID":
                    if(socketData[key] != None and not isinstance(socketData[key], str)):
                        raise Client_Error_Handler.BadRequest(message="Socket's \"" + key + "\" value must be string")
                    self.HAID = socketData["HAID"]
                        
                case "MAC":
                    if(not isinstance(socketData[key], str) or not isaMAC(socketData[key])):
                        raise Client_Error_Handler.BadRequest(message="Socket's \"" + key + "\" value must be a valid MAC address")
                    match key:
                        case "MAC": self.MAC = socketData["MAC"]

                case "masterNode":
                    if(not isinstance(socketData[key], bool)):
                        raise Client_Error_Handler.BadRequest(message="Socket's \"" + key + "\" value must be boolean")
                    self.masterNode = socketData["masterNode"]
                
                case "RSSI":
                    if(not isinstance(socketData[key], (int, float))):
                        raise Client_Error_Handler.BadRequest(message="Socket's \"" + key + "\" value must be a number")
                    self.RSSI = socketData["RSSI"]

    def to_dict(self):
        result = {}
        for key in self.socketKeys:
            result[key] = getattr(self, key)
            
        return result
    
    def save2DB(self, DBPath):
        try:            
            if(check_presence_inDB(DBPath, "Sockets", "deviceID", self.deviceID)):
                raise Client_Error_Handler.BadRequest(message="Socket already connected to a device")
            
            if(check_presence_inDB(DBPath, "Sockets", "MAC", self.MAC)):
                raise Client_Error_Handler.BadRequest(message="Socket MAC address already exists in DB")
            
            save_entry2DB(DBPath, "Sockets", self.to_dict())
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while saving socket with deviceID \""
                + self.deviceID + "\" to the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while saving socket with deviceID \""
                + self.deviceID + "\" to the DB:\u0085\u0009" + str(e)
            )
        
    def updateDB(self, DBPath):
        try:            
            if(check_presence_inDB(DBPath, "Sockets", "deviceID", self.deviceID)):
                query = "SELECT socketID FROM Sockets WHERE deviceID = \"" + self.deviceID + "\""
                result = DBQuery_to_dict(DBPath, query)
                if(not result[0]["socketID"] == self.socketID):
                    raise Client_Error_Handler.BadRequest(message="Socket already connected to a device")
            
            if(check_presence_inDB(DBPath, "Sockets", "MAC", self.MAC)):
                query = "SELECT socketID FROM Sockets WHERE MAC = \"" + self.MAC + "\""
                result = DBQuery_to_dict(DBPath, query)
                if(not result[0]["socketID"] == self.socketID):
                    raise Client_Error_Handler.BadRequest(message="Socket already connected to another MAC address")
            
            update_entry_inDB(DBPath, "Sockets", "deviceID", self.to_dict())
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while updating socket with deviceID \"" + 
                self.socketID + "\" in the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while updating socket with ID \"" + 
                self.socketID + "\" in the DB:\u0085\u0009" + str(e)
            )
        
    def set2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "Sockets", "socketID", self.socketID)):
                self.updateDB(DBPath)
            else:
                self.save2DB(DBPath)
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while setting socket with ID \"" + 
                self.socketID + "\" in the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while setting socket with ID \"" + 
                self.socketID + "\" in the DB:\u0085\u0009" + str(e)
            )
        
    def deleteFromDB(DBPath, entry):
        try:
            if(not check_presence_inDB(DBPath, entry["table"], entry["keyName"], entry["keyValue"])):
                raise Client_Error_Handler.NotFound(message="Socket not found in DB")
            
            delete_entry_fromDB(DBPath, entry["table"], entry["keyName"], entry["keyValue"])
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while deleting socket with" + entry["keyName"] + " \"" + 
                entry["keyValue"] + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while deleting socket with" + entry["keyName"] + " \"" + 
                entry["keyValue"] + "\" from the DB:\u0085\u0009" + str(e)
            )
        
    def DB_to_dict(DBPath, socket):
        try:
            socketID = socket["socketID"]
            query = "SELECT * FROM Sockets WHERE socketID = \"" + socketID + "\""
            result = DBQuery_to_dict(DBPath, query)

            return result
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while retrieving socket with ID \"" + 
                socketID + "\" from the DB:\u0085\u0009" + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message="An error occurred while retrieving socket with ID \"" +
                socketID + "\" from the DB:\u0085\u0009" + str(e)
            )