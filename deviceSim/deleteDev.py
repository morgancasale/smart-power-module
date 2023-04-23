from myMQTT import myMQTT
import time
import random
import json

broker = "192.168.2.163"
brokerPort = 1883

clientID = "sensorSim"

usr = "admin"
pwd = "oppioppi"

Client = myMQTT(clientID, broker, brokerPort, usr, pwd)
Client.start()

system = "smartSockets"
deviceID = "SSCK1"

discoveryTopics = [
    "homeassistant/sensor/"+ system + "/"+ deviceID,
    "homeassistant/switch/"+ system + "/"+ deviceID
]

device_classes = ["voltage", "current", "power", "energy"]
for device_class in device_classes:
    dT = discoveryTopics[0] + "_" + device_class + "/config"
    print(Client.Publish(dT, "", retain=True))

plugs = [0, 1, 2]
for plug in plugs:
    dT = discoveryTopics[1] + "_" + str(plug) + "/config"
    print(Client.Publish(dT, "", retain=True))