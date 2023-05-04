import json
import requests
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *
from microserviceBase.Error_Handler import *
from microserviceBase import randomB64String


        
class DataHandler():
      
     
      
                       
              
      
      def regData_toHa(self, topic, payload):
        try:
            print("Topic: %s, Payload: %s" % (topic, payload))
            self.system = self.generalConfigs["CONFIG"]["HomeAssistant"]["system"]
            self.baseTopic = self.generalConfigs["CONFIG"]["HomeAssistant"]["baseTopic"]
               
            if(DataHandler.checkPresenceOfIDSocket(payload["deviceID"])): 
                if(not DataHandler.setStatusDevice(payload["deviceID"], "ONLINE")):
                    raise Server_Error_Handler.InternalServerError(
                        message = "An error occurred while updating device status"
                    )
                self.baseTopic += "/"
                stateSensorTopic = self.baseTopic + "/sensor/" + self.system + "/" + payload["deviceID"] + "/state"
            else: 
                raise Client_Error_Handler.NotFound("Device that sending data is not registered")
            DataHandler.checkpayload(payload)
            datafixed = {"Voltage": payload["VOltage"], "Current":payload["Current"], "Power":payload["Power"],"Energy": payload["Energy"]  }   
            self.MQTTService.Client.Publish(stateSensorTopic, json.dumps(datafixed))     
                 
        except HTTPError as e:
            msg = """
                An error occurred while 
                registering DATA to HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = msg)
        except Exception as e:
            msg = """
                An error occurred while
                registering DATA to HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(msg=msg)          
         
     

      def checkpayload(payload):
        configParams = sorted["socketID", "Voltage", "Current","Power","Energy"]
       
        if(not configParams == sorted(payload.keys())):
            raise HTTPError(
            "Missing parameters in config file")
        
        if (not isinstance(payload["socketID"], str)):
            raise Server_Error_Handler.BadRequest(
                "socketID parameter must be a string")
        

        if (not isinstance(payload["Voltage"], float)):
            raise Server_Error_Handler.BadRequest(
                "Voltage parameter must be a float")
        

        if (not isinstance(payload["Current"], float)):
            raise Server_Error_Handler.BadRequest(
                "Current parameter must be a float")
        

        if (not isinstance(payload["Power"], float)):
            raise Server_Error_Handler.BadRequest(
                "Power parameter must be a float")
    

        if (not isinstance(payload["Energy"], float)):
            raise Server_Error_Handler.BadRequest(
                "Energy parameter must be a float") 
     
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
          
            
      def setStatusDevice(deviceID, status, catalogAddress, catalogPort):
        try:
            url = "%s:%s/setStatus" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "Sockets",
                "keyName": "deviceID",
                "keyValue": deviceID,
                "status": status
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
