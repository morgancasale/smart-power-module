import json
import requests
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.Error_Handler import *

class commandHandler():
      
     def getCMD_fromHA(self, topic, payload):

        try:
            system = self.generalConfigs["CONFIG"]["HomeAssistant"]["system"]
            baseTopic = self.generalConfigs["CONFIG"]["HomeAssistant"]["baseTopic"]
            catalogAddress = self.generalConfigs["REGISTRATION"]["catalogAddress"]
            catalogPort = self.generalConfigs["REGISTRATION"]["catalogPort"]
            
            info = commandHandler.checkTopic(topic,baseTopic,system,catalogAddress, catalogPort)
                
            if (commandHandler.checkPresenceOfIDSocket(info[0] ,catalogAddress, catalogPort)):
               
                payload = json.loads(payload)
                commandHandler.checkPayload(payload)
            
                baseTopic += "/"
                cmdSensorTopic = (
                         "/smartSocket/control"
                    )    
                datafixed = {
                    "deviceID": info[0],
                    "plug": info[1],
                    "state": int(payload)

                }
                self.Publish(cmdSensorTopic, json.dumps(datafixed))
                
            else:
                raise Client_Error_Handler.NotFound(
                    "Device that sending data is not registered"
                )
        except HTTPError as e:
            message = (
                """
                An error occurred while 
                registering DATA to HomeAssistant: \u0085\u0009
            """
                + e._message
            )
            raise HTTPError(status=e.status, message=message)
            
        except Exception as e:
            message = """
                An error occurred while
                registering DATA to HomeAssistant: \u0085\u0009
            """ + str(
                e
            )
            raise Server_Error_Handler.InternalServerError(message=message)
    
     def checkTopic(topic, baseTopic,system,deviceID,plug):
         topic = topic.split("/")
         configParams = ["cmd_HA", baseTopic, system]
         if(not all(x in topic for x in configParams)):
            raise HTTPError("Missing parameters in topic")
         deviceID = topic[3]
         plug = topic[4]
         return [deviceID,plug]
     
     def checkPayload(payload):
        
         
         if not isinstance(payload, bool):
            raise Server_Error_Handler.InternalServerError("socketID parameter must be a string")

     def checkPresenceOfIDSocket(deviceID, catalogAddress, catalogPort):
        try:
            url = "%s:%s/checkPresence" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "Sockets",
                "keyName": "deviceID",
                "keyValue": deviceID
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

