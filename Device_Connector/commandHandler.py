import json
import requests
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
from microserviceBase.Error_Handler import *
from microserviceBase import randomB64String

def notify(topic, payload):
     print("Topic: %s, Payload: %s" % (topic, payload))
     commandHandler.checkPresenceOfIDSocket(topic.split("/") )#prendo ID da socket
     commandHandler.checkCMD(payload)

class commandHandler():
      
     def getCMD_fromHA():
          
          commandHandler.subCMD_fromHA()
          

     
     def subCMD_fromHA():
          
          a.MQTT.Subscribe("Dovepigliodati")
          while(True):
               time.sleep(1000)   
     def checkCMD(payload):
         configParams = sorted["CMD_HA"]
         if(not configParams == sorted(payload.keys())):
            raise HTTPError(
            "Missing parameters in config file")
        

     def checkPresenceOfIDSocket(socketID, catalogAddress, catalogPort):
        try:
            url = "%s:%s/checkPresence" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "Sockets",
                "keyName": "socketID",
                "keyValue": socketID
            }

            response = requests.get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)
            

            return result["result"]
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))

if __name__ == "__main__":
    a = ServiceBase("DEVConnector/fraSubFile.json", Notifier = notify)
    a.start()
    reg = commandHandler()
    reg.getCMD_fromHA()               