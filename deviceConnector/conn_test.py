import os
import time
import sys
import json

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

def REST_init(self):
    self.i = 0

def getSocketTopics():
    try:
        url = "%s:%s/getInfo" % (
            server.registerService.catalogAddress,
            str(server.registerService.catalogPort)
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
        raise server.clientErrorHandler.BadRequest(msg="An error occurred while getting MQTT broker: \u0085\u0009" + e._message)
    except Exception as e:
        raise server.serverErrorHandler.InternalServerError(msg="An error occurred while getting MQTT broker: \u0085\u0009" + str(e))

def GET(self, *uri, **params):
    try:
        data = {}
        out = {}
        if(checkPresenceOfSocket(params["MAC"])): # if the socket is already registered
            data = getSocket(params["MAC"])[0][0]
        else:
            data = regSocket(params["MAC"], float(params["RSSI"]))[0][0]

        out["socketID"] = data["socketID"]
        out["masterNode"] = data["masterNode"]

        if(params["autoBroker"]):
            broker = self.getMQTTBroker()
            out["brokerIP"] = broker["IPAddress"]
            out["brokerPort"] = broker["port"]
            out["brokerUser"] = broker["MQTTUser"]
            out["brokerPassword"] = broker["MQTTPassword"]

        if(params["autoTopics"]):
            topics = getSocketTopics()
            out["subTopic"] = topics["sub"]
            out["pubTopic"] = topics["pub"]

        return json.dumps(out)
    except HTTPError as e:
        raise HTTPError(status=e.status, message=e._message)
    except Exception as e:
        raise HTTPError(status=500, message=str(e))

def notifier(topic, payload):
    data = json.loads(payload)
    print("The temperature is: " + str(data["temperature"]) + "°C")

configFile_loc = "deviceConnector.json"
if(not IN_DOCKER): configFile_loc = "deviceConnector/" + configFile_loc
server = ServiceBase(configFile_loc, GET=GET, init_REST_func=REST_init, Notifier=notifier)
server.start()

def translateMAC(MAC):
    return [int(c,16) for c in MAC.split(":")]

def checkPresenceOfSocket(MAC):
    try:
        url = "%s:%s/checkPresence" % (
            server.registerService.catalogAddress,
            str(server.registerService.catalogPort)
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

def getSocket(MAC):
    try:
        url = "%s:%s/getInfo" % (
            server.registerService.catalogAddress,
            str(server.registerService.catalogPort)
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

def genSocketID():
    try:
        existence = True
        while(existence):
            newID = "SKT" + randomB64String(6)

            url = "%s:%s/checkPresence" % (
                server.registerService.catalogAddress,
                str(server.registerService.catalogPort)
            )
            params = {
                "table" : "Sockets",
                "keyName" : "socketID",
                "keyValue" : newID
            }

            response = get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            existence = json.loads(response.text)["result"]
    except HTTPError as e:
        raise HTTPError(status=e.status, message=e._message)
    except Exception as e:
        raise HTTPError(status=500, message=str(e))

    return newID

def genSocket(MAC, deviceID, RSSI):
    socket = {}
    try:
        socket["socketID"] = genSocketID()
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



def regSocket(MAC, RSSI):
    try:
        url = "%s:%s/regSocket" % (
            server.registerService.catalogAddress,
            str(server.registerService.catalogPort)
        )

        headers = {
            'content-type': "application/json",
        }

        payload = genSocket(MAC, "D"+randomB64String(6), RSSI)
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if(response.status_code != 200):
            raise HTTPError(response.status_code, str(response.text))
        return payload
    except HTTPError as e:
        raise HTTPError(status=e.status, message=e._message)
    except Exception as e:
        raise HTTPError(status=500, message=str(e))




server.MQTT.Subscribe("smartSocket/data")



while True:
    server.MQTT.Publish("smartSocket/control", {"socketID": "SKTNzA1MT", "state" : 1})
    time.sleep(5)
    server.MQTT.Publish("smartSocket/control", {"socketID": "SKTNzA1MT", "state" : 0})
    pass
    time.sleep(10)