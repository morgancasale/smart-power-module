import time
import json
import requests

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.Error_Handler import *
from microserviceBase import randomB64String

class SocketHandler():
    def checkPresenceOfSocket(MAC, catalogAddress, catalogPort):
        try:
            url = "%s:%s/checkPresence" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "Sockets",
                "keyName": "MAC",
                "keyValue": MAC
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
    
    def getSocket(MAC, catalogAddress, catalogPort):
        try:
            url = "%s:%s/getInfo" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "Sockets",
                "keyName": "MAC",
                "keyValue": MAC
            }

            response = requests.get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            result = json.loads(response.text)

            return result
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))
        
    def genSocketID(catalogAddress, catalogPort):
        try:
            existence = True
            while(existence):
                newID = "SKT" + randomB64String(6)

                url = "%s:%s/checkPresence" % (
                    catalogAddress,
                    str(catalogPort)
                )
                params = {
                    "table" : "Sockets",
                    "keyName" : "socketID",
                    "keyValue" : newID
                }

                response = requests.get(url, params=params)
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, str(response.text))
                
                existence = json.loads(response.text)["result"]

            return newID
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))
        
    def genSocket(MAC, deviceID, RSSI, catalogAddress, catalogPort):
        socket = {}
        try:
            socket["socketID"] = SocketHandler.genSocketID(catalogAddress, catalogPort)
            socket["MAC"] = MAC
            socket["deviceID"] = deviceID
            socket["masterNode"] = False
            socket["HAID"] = None
            socket["RSSI"] = RSSI
            return socket
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise HTTPError(status=500, message=str(e))
        
    def regSocket(self, catalogAddress, catalogPort, HAIP, HAPort, HAToken, system, baseTopic, MAC, RSSI):
        try:
            url = "%s:%s/setSocket" % (
                catalogAddress,
                str(catalogPort)
            )

            headers = {
                'content-type': "application/json",
            }

            payload = SocketHandler.genSocket(MAC, "D"+randomB64String(6), RSSI, catalogAddress, catalogPort)
            response = requests.put(url, headers=headers, data=json.dumps(payload))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            payload["masterNode"] = not SocketHandler.checkPresenceOfMasterNode(catalogAddress, catalogPort)

            SocketHandler.regSocket_toHA(self, system, baseTopic, payload["deviceID"], payload["masterNode"])

            HAID = SocketHandler.getHAID(HAIP, HAPort, HAToken, payload["deviceID"])
            payload["HAID"] = HAID
            
            response = requests.put(url, headers=headers, data=json.dumps(payload))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))      
            
            return payload
        except HTTPError as e:
            SocketHandler.delSocket_fromHA(self, payload["deviceID"], baseTopic, system)
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            SocketHandler.delSocket_fromHA(self, payload["deviceID"], baseTopic, system)
            raise HTTPError(status=500, message=str(e))
        
    def getSocketTopics(catalogAddress, catalogPort):
        try:
            url = "%s:%s/getInfo" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "EndPoints",
                "keyName": "endPointName",
                "keyValue": "socketControl"
            }

            response = requests.get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            return response.json()[0]["MQTTTopics"]
        except HTTPError as e:
            raise Client_Error_Handler.BadRequest(msg="An error occurred while getting MQTT broker: \u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(msg="An error occurred while getting MQTT broker: \u0085\u0009" + str(e))
    
    def checkPresenceOfMasterNode(catalogAddress, catalogPort):
        try:
            url = "%s:%s/checkPresence" % (
                catalogAddress,
                str(catalogPort)
            )
            params = {
                "table": "Sockets",
                "keyName": "masterNode",
                "keyValue": 1
            }

            response = requests.get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            return response.json()["result"]
        except HTTPError as e:
            raise Client_Error_Handler.BadRequest(msg="An error occurred while getting MQTT broker: \u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(msg="An error occurred while getting MQTT broker: \u0085\u0009" + str(e))

    def giveRole_toSocket(self, *uri, **params): #self è il self di REST
        catalogAddress = self.generalConfigs["REGISTRATION"]["catalogAddress"]
        catalogPort = self.generalConfigs["REGISTRATION"]["catalogPort"]
        try:
            data = {}
            out = {}
            if(SocketHandler.checkPresenceOfSocket(params["MAC"], catalogAddress, catalogPort)): # if the socket is already registered
                data = SocketHandler.getSocket(params["MAC"], catalogAddress, catalogPort)[0][0]
                data["masterNode"] = bool(data["masterNode"])
            else:
                HAIP = self.generalConfigs["CONFIG"]["HomeAssistant"]["address"]
                HAPort = self.generalConfigs["CONFIG"]["HomeAssistant"]["port"]
                HAToken = self.generalConfigs["CONFIG"]["HomeAssistant"]["token"]
                system = self.generalConfigs["CONFIG"]["HomeAssistant"]["system"]
                baseTopic = self.generalConfigs["CONFIG"]["HomeAssistant"]["baseTopic"]
                data = SocketHandler.regSocket(self, catalogAddress, catalogPort, HAIP, HAPort, HAToken, system, baseTopic, params["MAC"], float(params["RSSI"]))

            out["socketID"] = data["socketID"]
            out["masterNode"] = data["masterNode"]

            if(params["autoBroker"]):
                broker = self.getMQTTBroker()
                out["brokerIP"] = broker["IPAddress"]
                out["brokerPort"] = broker["port"]
                out["brokerUser"] = broker["MQTTUser"]
                out["brokerPassword"] = broker["MQTTPassword"]

            if(params["autoTopics"]):
                topics = SocketHandler.getSocketTopics(catalogAddress, catalogPort)
                out["subTopic"] = topics["sub"]
                out["pubTopic"] = topics["pub"]

            return json.dumps(out)
        except HTTPError as e:
            msg = """
                An error occurred while 
                registering socket to catalog: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = msg)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(msg=
                "An error occurred while getting MQTT broker: \u0085\u0009" + str(e)
            )

    def regSocket_toHA(self, system, baseTopic, deviceID, masterNode):
        try:
            baseTopic += "/"
            stateSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/state"
            availableSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/status"

            sensorsPayload = [
                {
                    "name": "Voltage",
                    "unit_of_measurement": "V",
                    "device_class": "voltage",
                    "value_template": "{{ value_json.voltage|default(0) }}"
                },
                {
                    "name": "Current",
                    "unit_of_measurement": "A",
                    "device_class": "current",
                    "value_template": "{{ value_json.current|default(0) }}"

                },
                {
                    "name": "Power",
                    "unit_of_measurement": "W",
                    "device_class": "power",
                    "value_template": "{{ value_json.power|default(0) }}"
                },
                {
                    "name": "Energy",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy|default(0) }}"
                }
            ]

            sensorsGeneralPayload = {
                "availability_topic": availableSensorTopic,
                "state_topic": stateSensorTopic
            }

            name = "Smart Socket " + ("Master " if bool(masterNode) else "") + deviceID

            devicePayload = {
                "unique_id": deviceID,
                "device": {
                    "name": name,
                    "identifiers": [deviceID],
                }
            }

            stateSwitchTopic = baseTopic + "switch/" + system + "/" + deviceID + "/state"
            commandSwitchTopic = baseTopic + "switch/" + system + "/" + deviceID + "/control"
            availableSwitchTopic = baseTopic + "switch/" + system + "/" + deviceID + "/status"

            switchesPayload = [
                {
                    "name": "Left plug",
                    "state_topic": stateSwitchTopic + "/0",
                    "command_topic": commandSwitchTopic + "/0",
                    "availability_topic": availableSwitchTopic+ "/0"
                },
                {
                    "name": "Center plug",
                    "state_topic": stateSwitchTopic + "/1",
                    "command_topic": commandSwitchTopic +"/1",
                    "availability_topic": availableSwitchTopic+"/1"
                },
                {
                    "name": "Right plug",
                    "state_topic": stateSwitchTopic + "/2",
                    "command_topic": commandSwitchTopic +"/2",
                    "availability_topic": availableSwitchTopic+"/2"
                }
            ]

            switchesGeneralPayload = {
                "device_class": "outlet",
                "payload_on": True,
                "payload_off": False,
                "state_on": True,
                "state_off": False
            }

            for sensor in sensorsPayload:
                sensor.update(sensorsGeneralPayload)
                sensor.update(devicePayload)
                sensor["unique_id"] = sensor["unique_id"] + "_" + sensor["device_class"]
                discTopic = baseTopic + "sensor/" + system + "/" + deviceID + "_" + sensor["device_class"] + "/config" # homeassistant/sensor/smartSocket/
                print(self.MQTTService.Client.publish(discTopic, json.dumps(sensor)))
                time.sleep(0.1)
                

            i = 0
            for switch in switchesPayload:
                switch.update(switchesGeneralPayload)
                switch.update(devicePayload)
                switch["unique_id"] = switch["unique_id"] + "_" + str(i)
                discTopic = baseTopic + "switch/" + system + "/" + deviceID + "_" + str(i) + "/config"
                print(self.MQTTService.Client.publish(discTopic, json.dumps(switch)))
                i+=1
                
        except HTTPError as e:
            msg = """
                An error occurred while 
                registering socket to HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = msg)
        except Exception as e:
            msg = """
                An error occurred while
                registering socket to HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(msg=msg)

    def delSocket_fromHA(self, deviceID, baseTopic, system):
        try:
            discoveryTopics = [
                baseTopic + "sensor/" + system + "/"+ deviceID,
                baseTopic + "switch/" + system + "/"+ deviceID
            ]

            device_classes = ["voltage", "current", "power", "energy"]
            for device_class in device_classes:
                dT = discoveryTopics[0] + "_" + device_class + "/config"
                print(self.MQTTService.Publish(dT, "", retain=True))

            plugs = [0, 1, 2]
            for plug in plugs:
                dT = discoveryTopics[1] + "_" + str(plug) + "/config"
                print(self.MQTTService.Publish(dT, "", retain=True))
        except HTTPError as e:
            msg = """
                An error occurred while 
                deleting socket from HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = msg)
        except Exception as e:
            msg = """
                An error occurred while
                deleting socket from HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(msg=msg)

    def getHAID(HAIP, HAPort, HAToken, deviceID):
        try:
            template = """{% set devices = states | map(attribute='entity_id') | map('device_id') | unique | reject('eq',None) | list %}
                {%- set ns = namespace(devices = []) %}
                {%- for device in devices %}
                {%- set ids = (device_attr(device, "identifiers") | list)[0] | list -%}
                {%- if \"""" + deviceID + """\" in ids %}
                    {%- set entities = device_entities(device) | list %}
                    {%- if entities %}
                    {%- set ns.devices = ns.devices + 
                    [ {
                        "name": device_attr(device, "name"), "entities" : entities, "identifiers" : ids
                        } ] %}
                    {%- endif %}
                {%- endif %}
                {%- endfor %}
                {{ ns.devices }}"""

            url = "%s:%s/api/template" % (
                HAIP, 
                str(HAPort)
            )

            HAToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzNjlmNWFiMzQ3Nzk0NTExYjAwZDE0YzA5ZTVkYmUwMCIsImlhdCI6MTY4MTczNzc2NiwiZXhwIjoxOTk3MDk3NzY2fQ.gn76jF7NYDzAxhW4tiQZ9kfD8K3TaTqGE__z_7xChOU"
            headers = {
                "Authorization": "Bearer " + HAToken,
                'content-type': "application/json",
            }

            response = requests.post(url, headers=headers, data=json.dumps({"template": template}))
            if(response.status_code != 200):
                raise HTTPError(status=response.status_code, message=response.text)
            
            text = response.text.replace("\'", "\"")
            response = json.loads(text)

            return response[0]["entities"][0].split("_")[1]
        except HTTPError as e:
            msg = """
                An error occurred while 
                getting devices info from Home Assistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = msg)
        except Exception as e:
            msg = """
                An error occurred while 
                getting devices info from Home Assistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(msg=msg)
    