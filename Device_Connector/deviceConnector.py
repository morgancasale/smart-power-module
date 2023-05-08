import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from threading import Thread
from colorama import Fore

from microserviceBase.serviceBase import *
from microserviceBase.Error_Handler import * 

from socketHandler import SocketHandler
from dataHandler import DataHandler
from commandHandler import commandHandler

def notify(self, topic, payload):
    print("Topic: %s, Payload: %s" % (topic, payload))
    Topic = topic.split("/")
    config_command = ["homeassistant","switch","smartSocket","control"]
    config_data = ["smartSocket","data"]
    if( all(x in Topic for x in config_command)):
        commandHandler.getCMD_fromHA(self,topic,payload)
    elif( all(x in Topic for x in config_data)):
        DataHandler.regData_toHa(self,topic,payload)
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
        #self.handleDelete_byHA = SocketHandler.handleDeleteSocket_byHA

        self.service = ServiceBase(
            "Device_Connector/deviceConnector.json", GET=self.regSocket_toCatalog, PUT=self.handleUpdate_toHA, 
            Notifier = notify
        )

        self.catalogAddress = self.service.generalConfigs["REGISTRATION"]["catalogAddress"]
        if("http://" not in self.catalogAddress):
            self.catalogAddress = "http://" + self.catalogAddress
        self.catalogPort = self.service.generalConfigs["REGISTRATION"]["catalogPort"]
 
        self.service.start()

        self.service.MQTT.Subscribe("smartSocket/data")
        self.service.MQTT.Subscribe("/homeassistant/switch/smartSocket/+/control")

        '''OnlineStatusTracker = Thread(target=self.OnlineStatusTracker, args=(self.catalogAddress, self.catalogPort))
        OnlineStatusTracker.start()'''

    '''def OnlineStatusTracker(self, catalogAddress, catalogPort):
        try:
            while True:
                watchDogTimer = 5*60

                url = "%s:%s/updateOnlineStatus"%(catalogAddress, catalogPort)
                params = [
                    {"table" : "Devices", "timer" : watchDogTimer}, 
                    {"table" : "DeviceResource_conn", "timer" : watchDogTimer}
                ]

                headers = {"Content-Type" : "application/json"}
                response = requests.patch(url, headers=headers, data=json.dumps(params))
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, response.text)
                
                print(Fore.LIGHTGREEN_EX + "Online status Tracker:\n\t%s"%response.text + Fore.RESET)

                time.sleep(watchDogTimer)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while updating devices online status" + str(e)
            )'''

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

    