import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)
    
from colorama import Fore

from microserviceBase.serviceBase import *
from microserviceBase.Error_Handler import * 

from socketHandler import SocketHandler
from dataHandler import DataHandler
from commandHandler import commandHandler

def notify(self, topic, payload):
    #print("Topic: %s, Payload: %s" % (topic, payload))
    Topic = topic.split("/")
    config_command = ["homeassistant","switch","smartSocket","control"]
    config_data = ["smartSocket","data"]
    control_data = ["smartSocket", "control"]
    if( all(x in Topic for x in config_command)):
        commandHandler.getCMD_fromHA(self, topic, payload)
    elif( all(x in Topic for x in config_data)):
        DataHandler.regData_toHa(self, topic, payload)
    elif( all(x in Topic for x in control_data)):
        DataHandler.control_HA(self, topic, payload)
    else:
        raise Client_Error_Handler.BadRequest("Topic not valid")


class DeviceConnector():
    def __init__(self):
        self.baseTopic = "homeassistant/"
        self.system = "smartSockets" #self.system mi fa schifo come termine centra nulla
         
        self.regSocket_toCatalog = SocketHandler.giveRole_toSocket 
        self.handleUpdate_toHA = SocketHandler.updateSocketName_onHA # mi salvo queste funzioni 
        self.regSocket_toHA = SocketHandler.regSocket_toHA           # perchè utilizzano i metodi
        self.delSocket_fromHA = SocketHandler.delSocket_fromHA       # del servizio
        self.regHouse_toHA = SocketHandler.regHouse_toHA
        #self.handleDelete_byHA = SocketHandler.handleDeleteSocket_byHA

        configFile_loc = "deviceConnector.json"
        if(not IN_DOCKER): configFile_loc = "deviceConnector/" + configFile_loc
        self.service = ServiceBase(
            configFile_loc,
            GET = self.regSocket_toCatalog, 
            PUT = self.handleUpdate_toHA, 
            Notifier = notify
        )

        self.catalogAddress = self.service.generalConfigs["REGISTRATION"]["catalogAddress"]
        if("http://" not in self.catalogAddress):
            self.catalogAddress = "http://" + self.catalogAddress
        self.catalogPort = self.service.generalConfigs["REGISTRATION"]["catalogPort"]
 
        self.service.start()

        #self.genHouseSensor()

        self.service.MQTT.Subscribe("smartSocket/data")
        self.service.MQTT.Subscribe("homeassistant/switch/smartSocket/+/control/#")
        self.service.MQTT.Subscribe("smartSocket/control")


    def setOnlineStatus(self, deviceID, status):
        try:
            url = "%s:%s/setOnlineStatus"%(self.catalogAddress, self.catalogPort)
            params = [
                {"table" : "Devices", "keyName" : "deviceID", "keyValue" : deviceID, "status" : status},
                {"table" : "DeviceResource_conn", "keyName" : "deviceID", "keyValue" : deviceID, "status" : status},
                {"table" : "DeviceSettings", "keyName" : "deviceID", "keyValue" : deviceID, "status" : status}
            ]

            headers = {"Content-Type" : "application/json"}
            response = requests.put(url, headers=headers, data=json.dumps(params))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, response.text)
        except HTTPError as e:
            raise HTTPError(
                e.code, "An error occurred while updating devices online status" + e._message
            ) 
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while updating devices online status" + str(e)
            )
            


service = DeviceConnector()

    