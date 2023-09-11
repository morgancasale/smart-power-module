import json
import requests
import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.Error_Handler import *


class DataHandler():
    def regData_toHa(self, topic, payload):
        try:
            print("Topic: %s, Payload: %s" % (topic, payload))
            self.system = self.generalConfigs["CONFIG"]["HomeAssistant"]["system"]
            self.baseTopic = self.generalConfigs["CONFIG"]["HomeAssistant"]["baseTopic"]
            self.catalogAddress = self.generalConfigs["REGISTRATION"]["catalogAddress"]
            self.catalogPort = self.generalConfigs["REGISTRATION"]["catalogPort"]
            payload = json.loads(payload)
            if (DataHandler.checkPresenceOfIDSocket(payload["deviceID"], self.catalogAddress, self.catalogPort)):
                if (not DataHandler.setStatusDevice(payload["deviceID"], 1,self.catalogAddress, self.catalogPort)):
                    raise Server_Error_Handler.InternalServerError(
                        message="An error occurred while updating device status"
                    )
                self.baseTopic += "/"
                stateSensorTopic = (
                    self.baseTopic
                    + "sensor/"
                    + self.system
                    + "/"
                    + payload["deviceID"]
                    + "/state"
                )
                availableSensorTopic = (
                    self.baseTopic
                    + "sensor/"
                    + self.system
                    + "/"
                    + payload["deviceID"]
                    + "/status"
                )
            else:
                raise Client_Error_Handler.NotFound(
                    "Device that sending data is not registered"
                )
            DataHandler.checkpayload(payload)
            
            datafixed = {
                "voltage": payload["Voltage"],
                "current": payload["Current"],
                "power": payload["Power"],
                "energy": payload["Energy"]
            }

            enabledSockets = DataHandler.getPlugEnabled(self.catalogAddress, self.catalogPort, payload["deviceID"])
            enabledSockets = ["online" if bool(int(x)) else "offline" for x in enabledSockets]

            self.Publish(availableSensorTopic, "online")
            switchAvaibilityTopic = self.baseTopic +"switch/" + self.system + "/" + payload["deviceID"] + "/status"
            for i in range(3):
                self.Publish(switchAvaibilityTopic + "/" + str(i), enabledSockets[i])

            switchStateTopic = self.baseTopic +"switch/" + self.system + "/" + payload["deviceID"] + "/state"
            self.Publish(stateSensorTopic, json.dumps(datafixed))
            for i in range(3):
                self.Publish(switchStateTopic + "/" + str(i), str(bool(payload["SwitchStates"][i])))


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
        
    def getPlugEnabled(catalogAddress, catalogPort, deviceID):
        try:
            url = "%s:%s/getInfo" % (catalogAddress, str(catalogPort))
            params = {"table": "DeviceSettings", "keyName": "deviceID", "keyValue": deviceID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            return result[0]["enabledSockets"]
        except HTTPError as e:
            raise HTTPError(status=e.status, message="An error occurred while getting socket settings: " + e._message)
        except Exception as e:
            raise HTTPError(status=500, message="An error occurred while getting socket settings: " + str(e))

    def checkpayload(payload):
        configParams = sorted(["deviceID", "Voltage", "Current", "Power", "Energy", "SwitchStates"])

        if not configParams == sorted(payload.keys()):
            raise HTTPError("Missing parameters in config file")

        if not isinstance(payload["deviceID"], str):
            raise Client_Error_Handler.BadRequest("socketID parameter must be a string")

        if not isinstance(payload["Voltage"], (int, float)):
            raise Client_Error_Handler.BadRequest("Voltage parameter must be a float")

        if not isinstance(payload["Current"], (int, float)):
            raise Client_Error_Handler.BadRequest("Current parameter must be a float")

        if not isinstance(payload["Power"], (int, float)):
            raise Client_Error_Handler.BadRequest("Power parameter must be a float")

        if not isinstance(payload["Energy"], (int, float)):
            raise Client_Error_Handler.BadRequest("Energy parameter must be a float")
        
        if not isinstance(payload["SwitchStates"], list):
            raise Client_Error_Handler.BadRequest("SwitchStates parameter must be a list")
        for switch in payload["SwitchStates"]:
            if(not isinstance(switch, (bool, int))):
                raise Client_Error_Handler.BadRequest("Switch parameter must be a int or bool")

    def checkPresenceOfIDSocket(deviceID, catalogAddress, catalogPort):
        try:
            url = "%s:%s/checkPresence" % (catalogAddress, str(catalogPort))
            params = {"table": "Sockets", "keyName": "deviceID", "keyValue": deviceID}

            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            return result["result"]
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))

    def setStatusDevice(deviceID, status, catalogAddress, catalogPort):
        try:
            url = "%s:%s/setOnlineStatus" % (catalogAddress, str(catalogPort))
            data = {
                "table": "Devices",
                "keyName": "deviceID",
                "keyValue": deviceID,
                "status": status,
            }

            response = requests.put(url, json=data)
            if response.status_code != 200:
                raise HTTPError(response.status_code, str(response.text))
            result = response.text

            return result
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))