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
         DataHandler.checkPresenceOfIDSocket(payload["socketID"])
         DataHandler.checkpayload(payload)
         DataHandler.FixData_fromESP(payload["socketID"],payload["Voltage"],payload["Current"],payload["Power"], payload["Energy"])

class DataHandler():
      
     def regData_toHa():
          
          DataHandler.subData_fromESP()
          

     
     def subData_fromESP():
          
          a.MQTT.Subscribe("smartSocket/data")
          while(True):
               time.sleep(1000)
     
     
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
       
             

     def FixData_fromESP(payload,Voltage,Current,Power, Energy): 
         fixedData={"Voltage": Voltage, "Current":Current, "Power":Power,"Energy": Energy}
         DataHandler.SendFixData(payload["socketID"],fixedData=fixedData)

     def SendFixData(socketID,fixedData):
        
          a.MQTT.Publish("homeassistant/sensor/smartSocket/"+ socketID +"/status", json.dumps(fixedData))
        
            
      
if __name__ == "__main__":

    a = ServiceBase("DEVConnector/fraSubFile.json", Notifier = notify)
    a.start()
    reg = DataHandler()
    reg.regData_toHa()