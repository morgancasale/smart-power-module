import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from threading import Thread

from microserviceBase.serviceBase import *
from microserviceBase.Error_Handler import * 

from socketHandler import SocketHandler

class DeviceConnector():
    def __init__(self):
        self.baseTopic = "homeassistant/"
        self.system = "smartSockets" #self.system mi fa schifo come termine centra nulla
         
        self.regSocket_toCatalog = SocketHandler.giveRole_toSocket 
        self.handleUpdate_toHA = SocketHandler.updateSocketName_onHA # mi salvo queste funzioni 
        self.regSocket_toHA = SocketHandler.regSocket_toHA           # perchè utilizzano i metodi
        self.delSocket_fromHA = SocketHandler.delSocket_fromHA       # del servizio
        #self.handleDelete_byHA = SocketHandler.handleDeleteSocket_byHA

        self.service = ServiceBase("Device_Connector/deviceConnector.json", GET=self.regSocket_toCatalog, PUT=self.handleUpdate_toHA, Notifier=None)

        self.catalogAddress = self.service.generalConfigs["REGISTRATION"]["catalogAddress"]
        self.catalogPort = self.service.generalConfigs["REGISTRATION"]["catalogPort"]
 
        self.service.start()

        OnlineStatusTracker = Thread(target=self.OnlineStatusTracker, args=(self.catalogAddress, self.catalogPort))
        OnlineStatusTracker.start()
        
        #self.service.MQTT.Subscribe("%s+/%s/+/config"%(self.baseTopic, self.system))

    def OnlineStatusTracker(catalogAddress, catalogPort):
        try:
            while True:
                url = "http://%s:%s/updateOnlineStatus"%(catalogAddress, catalogPort)
                params = [{"table" : "Devices" }, {"table" : "DeviceResource_conn"}]

                response = requests.patch(url, data=json.dumps(params))
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, response.text)

                time.sleep(5*60)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while updating devices online status" + str(e)
            )
        
    def setOnlineStatus(self, deviceID, status):
        try:
            url = "http://%s:%s/setOnlineStatus"%(self.catalogAddress, self.catalogPort)
            params = [
                {"table" : "Devices", "keyName" : "deviceID", "keyValue" : deviceID, "status" : status},
                {"table" : "DeviceResource_conn", "keyName" : "deviceID", "keyValue" : deviceID, "status" : status}
            ]

            response = requests.put(url, data=json.dumps(params))
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

    