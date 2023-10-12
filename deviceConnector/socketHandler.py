import time
import json
import requests
import socket

import os
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.Error_Handler import *
from microserviceBase.utility import randomB64String

from cherrypy import request as cherrypyRequest

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
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while checking the presence of the socket: " + str(e)
            )
    
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
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while getting the socket: " + str(e)
            )
        
    def genDeviceID(catalogAddress, catalogPort):
        try:
            existence = True
            while(existence):
                newID = "D" + randomB64String(6)

                url = "%s:%s/checkPresence" % (
                    catalogAddress,
                    str(catalogPort)
                )
                params = {
                    "table" : "Devices",
                    "keyName" : "deviceID",
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
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while generating the device ID: " + str(e)
            )
        
    def genEndPointID(catalogAddress, catalogPort):
        try:
            existence = True
            while(existence):
                newID = "EP" + randomB64String(6)

                url = "%s:%s/checkPresence" % (
                    catalogAddress,
                    str(catalogPort)
                )
                params = {
                    "table" : "EndPoints",
                    "keyName" : "endPointID",
                    "keyValue" : newID
                }

                response = requests.get(url, params=params)
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, str(response.text))
                
                existence = json.loads(response.text)["result"]
            
            return newID
        except HTTPError as e:
            raise HTTPError(
                status=e.status, message="An error occurred while generating an endPointID: " + e._message
            )
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while generating an endPointID: " + str(e)
            )

    def genResources():
        return [
            {
                "resourceID" : "RVOLT",
                "resourceName" : "Voltage",
                "resourceMode" : "read",
                "resourceType" : "float",
                "resourceUnit" : "V"
            },
            {
                "resourceID" : "RCURR",
                "resourceName" : "Current",
                "resourceMode" : "read",
                "resourceType" : "float",
                "resourceUnit" : "A"
            },
            {
                "resourceID" : "RPOW",
                "resourceName" : "Power",
                "resourceMode" : "read",
                "resourceType" : "float",
                "resourceUnit" : "W"
            },
            {
                "resourceID" : "RPOWH",
                "resourceName" : "Energy",
                "resourceMode" : "read",
                "resourceType" : "float",
                "resourceUnit" : "Wh"
            },
            {
                "resourceID" : "RSW0",
                "resourceName" : "Left_switch",
                "resourceMode" : "write",
                "resourceType" : "int",
                "resourceUnit" : "bool"
            },
            {
                "resourceID" : "RSW1",
                "resourceName" : "Center_switch",
                "resourceMode" : "write",
                "resourceType" : "int",
                "resourceUnit" : "bool"
            },
            {
                "resourceID" : "RSW2",
                "resourceName" : "Right_switch",
                "resourceMode" : "write",
                "resourceType" : "int",
                "resourceUnit" : "bool"
            }
        ]
    
    def genEndpoints(catalogAddress, catalogPort, system, baseTopic, deviceID):
        endPoint = {}
        endPoint["endPointID"] = SocketHandler.genEndPointID(catalogAddress, catalogPort)
        endPoint["endPointName"] = "Socket " + deviceID +" EndPoint"
        endPoint["protocols"] = ["MQTT"]
        endPoint["clientID"] = deviceID
        endPoint["MQTTTopics"] = SocketHandler.genTopics(system, baseTopic, deviceID)

        endPoint["IPAddress"] = None
        endPoint["port"] = None
        endPoint["CRUDMethods"] = None
        endPoint["MQTTUser"] = None
        endPoint["MQTTPassword"] = None
        endPoint["QOS"] = 0
        return endPoint


    def genDevice(catalogAddress, catalogPort, system, baseTopic, deviceID, deviceName, houseID):
        try:
            device = {}
            device["deviceID"] = deviceID
            device["deviceName"] = deviceName
            device["houseID"] = houseID

            device["Resources"] = SocketHandler.genResources()
            device["endPoints"] = [SocketHandler.genEndpoints(catalogAddress, catalogPort, system, baseTopic, deviceID)]
            return device
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while generating the device: " + str(e)
            )
    
    def genSocket(MAC, deviceID, masterNode):
        socket = {}
        try: 
            socket["deviceID"] = deviceID
            socket["MAC"] = MAC
            socket["masterNode"] = masterNode
            socket["HAID"] = None
            return socket
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while generating the socket: " + str(e)
            )
        
    def delDevice_fromCatalog(deviceID, catalogAddress, catalogPort):
        try:
            url = "%s:%s/delDevice" % (
                catalogAddress,
                str(catalogPort)
            )
            headers = {
                'content-type': "application/json",
            }
            params = {
                "deviceID" : deviceID
            }

            response = requests.delete(url, headers=headers, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            return True
        except HTTPError as e:
            raise HTTPError(status=e.status, message=e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while deleting the device from the catalog: " + str(e)
            )
        
    def genSocketStgs(deviceID, deviceName):
        socketStgs = {}
        socketStgs["deviceID"] = deviceID
        socketStgs["deviceName"] = deviceName
        socketStgs["enabledSockets"] = [1, 1, 1]
        socketStgs["HPMode"] = 0
        socketStgs["MPControl"] = 0
        socketStgs["maxPower"] = 1
        socketStgs["MPMode"] = "Notify"
        socketStgs["faultControl"] = 0
        socketStgs["parControl"] = 0
        socketStgs["parThreshold"] = 1
        socketStgs["parMode"] = "Manual"
        socketStgs["applianceType"] = "None"
        socketStgs["FBControl"] = 0
        socketStgs["FBMode"] = "Notify"
        socketStgs["Online"] = 1

        return socketStgs
        
    def regSocket(self, catalogAddress, catalogPort, HAIP, HAPort, HAToken, system, baseTopic, MAC, houseID, autoMasterNode):
        try:
            headers = {
                'content-type': "application/json",
            }
            
            if(autoMasterNode):
                masterNode = not SocketHandler.checkPresenceOfMasterNode(catalogAddress, catalogPort)
            else:
                masterNode = False

            deviceID = SocketHandler.genDeviceID(catalogAddress, catalogPort)

            deviceName = "Smart Socket " + ("Master " if bool(masterNode) else "") + deviceID

            socketData = SocketHandler.genSocket(MAC, deviceID, masterNode)
            socketStgsData = SocketHandler.genSocketStgs(deviceID, deviceName)
            deviceData = SocketHandler.genDevice(catalogAddress, catalogPort, system, baseTopic, deviceID, deviceName, houseID)

            url = "%s:%s/regDevice" % (
                catalogAddress,
                str(catalogPort)
            )
            response = requests.post(url, headers=headers, data=json.dumps(deviceData))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            url = "%s:%s/setDeviceSettings" % (
                catalogAddress,
                str(catalogPort)
            )
            response = requests.put(url, headers=headers, data=json.dumps(socketStgsData))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))

            url = "%s:%s/setSocket" % (
                catalogAddress,
                str(catalogPort)
            )
            response = requests.put(url, headers=headers, data=json.dumps(socketData))
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            socketData["masterNode"] = masterNode
            
            if(self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
                SocketHandler.regSocket_toHA(self, system, baseTopic, deviceID, socketData["masterNode"])
                SocketHandler.regSocketStats_toHA(self, system, baseTopic, deviceID, socketData["masterNode"])
                
                if(masterNode):
                    SocketHandler.regHouse_toHA(self, system, baseTopic)

                deviceData["HAID"] = None
                
                response = requests.put(url, headers=headers, data=json.dumps(socketData))
                if(response.status_code != 200):
                    raise HTTPError(response.status_code, str(response.text))
            
            return socketData
        except HTTPError as e:
            if(self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]): 
                SocketHandler.delSocket_fromHA(self, deviceID, baseTopic, system)
            SocketHandler.delDevice_fromCatalog(deviceID, catalogAddress, catalogPort)
            raise HTTPError(status=e.status, message = "An error occurred while registering the socket: " + e._message)
        except Exception as e:
            if(self.generalConfigs["CONFIG"]["HomeAssistant"]["enabled"]):
                SocketHandler.delSocket_fromHA(self, deviceID, baseTopic, system)
            SocketHandler.delDevice_fromCatalog(deviceID, catalogAddress, catalogPort)
            raise Server_Error_Handler.InternalServerError(
                message = "An error occurred while registering the socket: " + str(e)
            )
        
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
            raise Client_Error_Handler.BadRequest(message="An error occurred while getting MQTT broker: \u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while getting MQTT broker: \u0085\u0009" + str(e))
    
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
            raise Client_Error_Handler.BadRequest(message="An error occurred while checking the presence of the Master node: \u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while checking the presence of the Master node: \u0085\u0009" + str(e))

    def giveRole_toSocket(self, *uri, **params): #self è il self di REST
        match uri[0]:
            case "getRole":
                catalogAddress = self.generalConfigs["REGISTRATION"]["catalogAddress"]
                catalogPort = self.generalConfigs["REGISTRATION"]["catalogPort"]
                try:
                    data = {}
                    out = {}
                    if("autoMasterNode" in params.keys()):
                        autoMasterNode = params["autoMasterNode"] == "True"
                    else : 
                        autoMasterNode = True
                    if(SocketHandler.checkPresenceOfSocket(params["MAC"], catalogAddress, catalogPort)): # if the socket is already registered
                        data = SocketHandler.getSocket(params["MAC"], catalogAddress, catalogPort)[0][0]
                        data["masterNode"] = bool(data["masterNode"])
                    else:
                        HAIP = self.generalConfigs["CONFIG"]["HomeAssistant"]["address"]
                        HAPort = self.generalConfigs["CONFIG"]["HomeAssistant"]["port"]
                        HAToken = self.generalConfigs["CONFIG"]["HomeAssistant"]["token"]
                        system = self.generalConfigs["CONFIG"]["HomeAssistant"]["system"]
                        baseTopic = self.generalConfigs["CONFIG"]["HomeAssistant"]["baseTopic"]
                        houseID = self.generalConfigs["CONFIG"]["houseID"]
                        data = SocketHandler.regSocket(self, catalogAddress, catalogPort, HAIP, HAPort, HAToken, system, baseTopic, params["MAC"], houseID, autoMasterNode)
                        

                    out["deviceID"] = data["deviceID"]
                    out["masterNode"] = data["masterNode"]

                    if(params["autoBroker"]):
                        broker = self.getMQTTBroker()
                        out["brokerIP"] = broker["IPAddress"]
                        if(not IN_DOCKER and out["brokerIP"] == "127.0.0.1"):
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            s.settimeout(0)
                            s.connect(('10.254.254.254', 1))
                            out["brokerIP"] = s.getsockname()[0]
                        out["brokerPort"] = broker["port"]
                        out["brokerUser"] = broker["MQTTUser"]
                        out["brokerPassword"] = broker["MQTTPassword"]
                        out["IN_DOCKER"] = IN_DOCKER

                    if(params["autoTopics"]):
                        topics = SocketHandler.getSocketTopics(catalogAddress, catalogPort)
                        out["subTopic"] = topics["sub"]
                        out["pubTopic"] = topics["pub"]

                    return json.dumps(out)
                except HTTPError as e:
                    message = """
                        An error occurred while 
                        registering socket to catalog: \u0085\u0009
                    """ + e._message
                    raise HTTPError(status=e.status, message = message)
                except Exception as e:
                    raise Server_Error_Handler.InternalServerError(message=
                        "An error occurred while getting MQTT broker: \u0085\u0009" + str(e)
                    )
            case _:
                raise Server_Error_Handler.NotImplemented(message="Method not implemented")
        
    def checkIfMasterNode(catalogAddress, catalogPort, deviceID): #TODO Test this 
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
            
            return response.json()["masterNode"]
        except HTTPError as e:
            raise Client_Error_Handler.BadRequest(message="An error occurred while checking id socket is the Master node: \u0085\u0009" + e._message)
        except Exception as e:
            raise Server_Error_Handler.InternalServerError(message="An error occurred while checking id socket is the Master node: \u0085\u0009" + str(e))
    
    def genTopics(system, baseTopic, deviceID):
        topics = {
            "sub": [],
            "pub": []
        }

        baseTopic += "/"
        stateSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/state"
        availableSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/status"

        topics["pub"].append(stateSensorTopic)
        topics["pub"].append(availableSensorTopic)

        stateSwitchTopic = baseTopic + "switch/" + system + "/" + deviceID + "/state"
        commandSwitchTopic = baseTopic + "switch/" + system + "/" + deviceID + "/control"
        availableSwitchTopic = baseTopic + "switch/" + system + "/" + deviceID + "/status"

        for i in range(3):
            topics["pub"].append(stateSwitchTopic + "/" + str(i))
            topics["pub"].append(availableSwitchTopic + "/" + str(i))
            topics["sub"].append(commandSwitchTopic + "/" + str(i))

        return topics

    def regSocket_toHA(self, system, baseTopic, deviceID, masterNode, deviceName=None):
        try:
            baseTopic += "/"
            stateSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/state"
            availableSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/status"

            sensorsPayload = [
                {
                    "name": "Voltage",
                    "unit_of_measurement": "V",
                    "device_class": "voltage",
                    "value_template": "{{ value_json.voltage }}"
                },
                {
                    "name": "Current",
                    "unit_of_measurement": "A",
                    "device_class": "current",
                    "value_template": "{{ value_json.current }}"

                },
                {
                    "name": "Power",
                    "unit_of_measurement": "W",
                    "device_class": "power",
                    "value_template": "{{ value_json.power }}"
                },
                {
                    "name": "Energy",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy }}"
                }
            ]

            sensorsGeneralPayload = {
                "availability_topic": availableSensorTopic,
                "state_topic": stateSensorTopic
            }

            if(deviceName == None) : name = "Smart Socket " + ("Master " if bool(masterNode) else "") + deviceID
            else : name = deviceName + (" Master " if bool(masterNode) else "")

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
                print(self.MQTTService.Publish(discTopic, json.dumps(sensor), retain=True))
                time.sleep(0.1)

            i = 0
            for switch in switchesPayload:
                switch.update(switchesGeneralPayload)
                switch.update(devicePayload)
                switch["unique_id"] = switch["unique_id"] + "_" + str(i)
                discTopic = baseTopic + "switch/" + system + "/" + deviceID + "_" + str(i) + "/config"
                print(self.MQTTService.Publish(discTopic, json.dumps(switch), retain=True))
                i+=1

                
                
        except HTTPError as e:
            message = """
                An error occurred while 
                registering socket to HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        except Exception as e:
            message = """
                An error occurred while
                registering socket to HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
    def regSocketStats_toHA(self, system, baseTopic, deviceID, masterNode, deviceName=None):
        try:
            baseTopic += "/"
            stateSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/state"
            availableSensorTopic = baseTopic + "sensor/" + system + "/" + deviceID + "/status"

            stat_sensorsPayload = [
                {
                    "name": "Hourly Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_HAvg }}"
                },
                {
                    "name": "Hourly Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_HTot }}"
                },
                {
                    "name": "Daily Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_DAvg }}"
                },
                {
                    "name": "Daily Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_DTot }}"
                },
                {
                    "name": "Monthly Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_MAvg }}"
                },
                {
                    "name": "Monthly Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_MTot }}"
                },
                {
                    "name": "Yearly Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_YAvg }}"
                },
                {
                    "name": "Yearly Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_YTot }}"
                }
            ]

            sensorsGeneralPayload = {
                "availability_topic": availableSensorTopic,
                "state_topic": stateSensorTopic
            }

            if(deviceName == None) : name = "Smart Socket " + ("Master " if bool(masterNode) else "") + deviceID
            else : name = deviceName + (" Master " if bool(masterNode) else "")

            deviceID = u"\u200B" + deviceID + "_stats"

            devicePayload = {
                "unique_id": deviceID,
                "device": {
                    "name": name + " Statistics",
                    "identifiers": [deviceID],
                }
            }

            for sensor in stat_sensorsPayload:
                sensor.update(sensorsGeneralPayload)
                sensor.update(devicePayload)
                stat = sensor["value_template"].split("energy_")[1].split(" ")[0]
                device_class = sensor["device_class"] + "_" + stat
                sensor["unique_id"] = sensor["unique_id"] + "_" + device_class
                discTopic = baseTopic + "sensor/" + system + "/" + deviceID + "_" + device_class + "/config" # homeassistant/sensor/smartSocket/
                print(self.MQTTService.Publish(discTopic, json.dumps(sensor), retain=True))
                time.sleep(0.1)                
                
        except HTTPError as e:
            message = """
                An error occurred while 
                registering socket to HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        except Exception as e:
            message = """
                An error occurred while
                registering socket to HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
    def regHouse_toHA(self, system, baseTopic):
        try:
            baseTopic += "/"
            stateSensorTopic = baseTopic + "sensor/" + system + "/" + "house" + "/state"
            availableSensorTopic = baseTopic + "sensor/" + system + "/" + "house" + "/status"

            stat_sensorsPayload = [
                {
                    "name": "Hourly Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_HAvg }}"
                },
                {
                    "name": "Hourly Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_HTot }}"
                },
                {
                    "name": "Daily Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_DAvg }}"
                },
                {
                    "name": "Daily Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_DTot }}"
                },
                {
                    "name": "Monthly Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_MAvg }}"
                },
                {
                    "name": "Monthly Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_MTot }}"
                },
                {
                    "name": "Yearly Average",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_YAvg }}"
                },
                {
                    "name": "Yearly Total",
                    "unit_of_measurement": "kWh",
                    "device_class": "energy",
                    "value_template": "{{ value_json.energy_YTot }}"
                }
            ]

            sensorsGeneralPayload = {
                "availability_topic": availableSensorTopic,
                "state_topic": stateSensorTopic
            }

            name = "House Statistics"

            devicePayload = {
                "unique_id": "H1",
                "device": {
                    "name": name,
                    "identifiers": ["H1"],
                }
            }

            for sensor in stat_sensorsPayload:
                sensor.update(sensorsGeneralPayload)
                sensor.update(devicePayload)
                stat = sensor["value_template"].split("energy_")[1].split(" ")[0]
                device_class = sensor["device_class"] + "_" + stat
                sensor["unique_id"] = sensor["unique_id"] + "_" + device_class
                discTopic = baseTopic + "sensor/" + system + "/" + "house" + "_" + device_class + "/config" # homeassistant/sensor/smartSocket/
                print(self.MQTTService.Publish(discTopic, json.dumps(sensor), retain=True))
                time.sleep(0.1)
        except HTTPError as e:
            message = """
                An error occurred while 
                registering house sensor to HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        
        except Exception as e:
            message = """
                An error occurred while
                registering house sensor to HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)



        
    def updateSocketName_onHA(self, *uri): #TODO Test this 
        try:
            match uri[1]:
                case "updateDeviceName":
                    params = cherrypyRequest.json
                    deviceID = params["deviceID"]
                    deviceName = params["deviceName"]

                    system = self.generalConfigs["CONFIG"]["HomeAssistant"]["system"]
                    baseTopic = self.generalConfigs["CONFIG"]["HomeAssistant"]["baseTopic"]
                    catalogAddress = self.generalConfigs["REGISTRATION"]["catalogAddress"]
                    catalogPort = self.generalConfigs["REGISTRATION"]["catalogPort"]
                    masterNode = self.checkIfMasterNode(catalogAddress, catalogPort, deviceID)

                    SocketHandler.regSocket_toHA(self, system, baseTopic, deviceID, masterNode, deviceName)
                
                case _:
                    raise Server_Error_Handler.NotImplemented("Method not implemented")
        except HTTPError as e:
            message = """
                An error occurred while 
                updating socket name on HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        except Exception as e:
            message = """
                An error occurred while
                updating socket name on HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)


    def delSocket_fromHA(self, deviceID, baseTopic, system):
        try:
            baseTopic += "/"
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
            message = """
                An error occurred while 
                deleting socket from HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        except Exception as e:
            message = """
                An error occurred while
                deleting socket from HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
        
    '''def handleDeleteSocket_byHA(topic, payload):
        try:
            if(payload==""):
                deviceID = topic.split("/")[-2]

                url = "http://%s:%s/delSocket" % (self.generalConfigs["REGISTRATION"]["catalogAddress"], self.generalConfigs["REGISTRATION"]["catalogPort"])
                params = {"table": "Sockets", "keyName" : "deviceID", "keyValue" : deviceID}

                response = requests.delete(url, params=params)
                if(response.status_code != 200):
                    raise HTTPError(status=response.status_code, message = response.text)

        except HTTPError as e:
            message = """
                An error occurred while 
                handling Deletion of Device initiated by HomeAssistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        except Exception as e:
            message = """
                An error occurred while
                handling Deletion of Device initiated by HomeAssistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)'''
    
    def getHAID(HAIP, HAPort, HAToken, deviceID):
        """
        Get the number that HomeAssistant assigns to a specific device
        for its entities (e.g. sensor.voltage_1, sensor.voltage_2, etc.)
        If the device is the first one to be registered, the function will return 0
        but no number will be appended to the entities (e.g. sensor.voltage, sensor.current, etc.)

        """

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

            if(not "_" in response[0]["entities"][0]): # If the device is the first one then it has no "HAID"
                return 0                               # So if return 0 then no "HAID" is needed
            else:
                return response[0]["entities"][0].split("_")[1]
        except HTTPError as e:
            message = """
                An error occurred while 
                getting devices info from Home Assistant: \u0085\u0009
            """ + e._message
            raise HTTPError(status=e.status, message = message)
        except Exception as e:
            message = """
                An error occurred while 
                getting devices info from Home Assistant: \u0085\u0009
            """ + str(e)
            raise Server_Error_Handler.InternalServerError(message=message)
    