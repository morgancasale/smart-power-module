from utility import *
from device import *

class DevCluster:
    def __init__(self, devClusterData, newDevCluster = False):
        self.devClusterKeys = ["devClustID", "Name"]
        self.connTables = ["ClusterDev_conn"]

        if(newDevCluster) : self.checkKeys(devClusterData)
        self.checkSaveValues(devClusterData)

        self.devClusterData = devClusterData

        if(newDevCluster):
            self.lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def checkKeys(self, devClusterData):
        if(not all(key in devClusterData.keys() for key in self.devClusterKeys)):
            raise HTTPError(status=400, message="Missing one or more keys")

    def checkSaveValues(self, devClusterData):
        for key in devClusterData.keys():
            match key:
                case ("devClustID" | "Name"):
                    if(not isinstance(devClusterData[key], str)):
                        raise HTTPError(status=400, message="Device Cluster's \"" + key + "\" parameter must be a string")
                    match key:
                        case "devClustID":
                            self.devClustID = devClusterData["devClustID"]
                        case "Name":
                            self.name = devClusterData["Name"]
                case "deviceID":
                    if(not all(isinstance(deviceID, str) for deviceID in devClusterData["deviceID"])):
                        raise HTTPError(status=400, message="Device Cluster's \"deviceID\" parameter must be a list of strings")
                    self.deviceID = devClusterData["deviceID"]

                case _:
                    raise HTTPError(status=400, message="Unexpected key \"" + key + "\"")
        

    def to_dict(self):
        result = {}

        for key in self.devClusterData.keys():
            match key:
                case ("devClustID" | "Name"):
                    result[key] = self.devClusterData[key]

        result["lastUpdate"] = self.lastUpdate

        return result

    def save2DB(self, DBPath):
        try:
            if(check_presence_inDB(DBPath, "DevClusters", "devClustID", self.devClustID)):
                raise HTTPError(status=400, message="An devCluster with ID \"" + self.devClustID + "\" already exists in the database")
            
            self.Online = True
            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            if("deviceID" in self.devClusterData.keys()):
                for deviceID in self.deviceID:
                    if(not check_presence_inDB(DBPath, "Devices", "deviceID", deviceID)):
                        raise HTTPError(status=400, message="Device with ID \"" + deviceID + "\" does not exist in the database")

                    save_entry2DB(DBPath, self.connTables[0], {"devClustID": self.devClustID, "deviceID": deviceID, "Online" : self.Online, "lastUpdate": self.lastUpdate})

            save_entry2DB(DBPath, "DevClusters", self.to_dict())
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while saving Device Cluster with ID \"" + self.devClustID + "\" to the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while saving Device Cluster with ID \"" + self.devClustID + "\" to the DB:\n\t" + str(e))

    def updateDB(self, DBPath):
        try:
            if(not check_presence_inDB(DBPath, "DevClusters", "devClustID", self.devClustID)):
                raise HTTPError(status=400, message="Device Cluster with ID \"" + self.devClustID + "\" does not exist in the database")
            

            self.lastUpdate = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            
            update_entry_inDB(DBPath, "DevClusters", "devClustID", self.to_dict())
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while updating Device Dluster with ID \"" + self.devClustID + "\" in the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while updating Device Cluster with ID \"" + self.devClustID + "\" in the DB:\n\t" + str(e))

    def deleteFromDB(DBPath, params):
        try:
            connTables = ["ClusterDev_conn"]
            if(not check_presence_inDB(DBPath, "DevClusters", "devClustID", params["devClustID"])):
                raise HTTPError(status=400, message="Device Cluster with ID \"" + params["devClustID"] + "\" does not exist in the database")

            for connTable in connTables:
                delete_entry_fromDB(DBPath, connTable, "devClustID", params["devClustID"])
            Device.cleanDB(DBPath)

            delete_entry_fromDB(DBPath, "DevClusters", "devClustID", params["devClustID"])
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while deleting Device Cluster with ID \"" + params["devClustID"] + "\" from the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while deleting Device Cluster with ID \"" + params["devClustID"] + "\" from the DB:\n\t" + str(e))
        return True

    def DB_to_dict(DBPath, devCluster):
        try:
            connTables = ["ClusterDev_conn"]
            tablesNames = ["Devices"]
            varsIDs = ["deviceID"]
            devClustID = devCluster["devClustID"]
            devClusterData = {"devClustID": devClustID, "Name": devCluster["Name"], "users": [], "Devices": []}

            
            if(check_presence_inDB(DBPath, connTables[0], "devClustID", devClustID)):
                query = "SELECT * FROM " + connTables[0] + " WHERE devClustID = \"" + devClustID + "\""
                Cluster_dev_conns = DBQuery_to_dict(DBPath, query)
                
                deviceIDs = "(\"" + "\", \"".join([Cluster_dev_conn[varsIDs[0]] for Cluster_dev_conn in Cluster_dev_conns]) + "\")"
                query = "SELECT * FROM " + tablesNames[0] + " WHERE " + varsIDs[0] + " in " + deviceIDs
                results = DBQuery_to_dict(DBPath, query)
                
                for result in results:
                    devClusterData["Devices"].append(Device.DB_to_dict(DBPath, result))

            return devClusterData
        except HTTPError as e:
            raise HTTPError(status=400, message="An error occurred while retrieving Device Cluster with ID \"" + devClustID + "\" from the DB:\n\t" + e._message)
        except Exception as e:
            raise HTTPError(status=400, message="An error occurred while retrieving Device Cluster with ID \"" + devClustID + "\" from the DB:\n\t" + str(e))