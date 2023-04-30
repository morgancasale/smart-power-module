from myMQTT import myMQTT
import time
import random
import json

broker = "192.168.2.163"
brokerPort = 1883

clientID = "sensorReg"

usr = "admin"
pwd = "oppioppi"

def notifier(topic, payload):
    print(topic, payload)

Client = myMQTT(clientID, broker, brokerPort, usr, pwd, notifier)
Client.start()

baseTopic = "homeassistant/"
system = "smartSockets"
deviceID = "SSCK1"
identifier = "SmartSocket"

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

devicePayload = {
    "unique_id": deviceID,
    "device": {
        "name": "Smart Socket " + deviceID,
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
    discTopic = baseTopic + "sensor/" + system + "/" + deviceID + "_" + sensor["device_class"] + "/config"
    print(Client.Publish(discTopic, json.dumps(sensor)))

i = 0
for switch in switchesPayload:
    switch.update(switchesGeneralPayload)
    switch.update(devicePayload)
    switch["unique_id"] = switch["unique_id"] + "_" + str(i)
    discTopic = baseTopic + "switch/" + system + "/" + deviceID + "_" + str(i) + "/config"
    print(Client.Publish(discTopic, json.dumps(switch)))
    i+=1

Client.Subscribe(switchesPayload[0]["command_topic"])
while(True):
    print(Client.Publish(availableSensorTopic, "online"))
    for switch in switchesPayload:
        print(Client.Publish(switch["availability_topic"], "online"))

    payload = {
        "voltage": round(random.uniform(200, 600)),
        "current": round(random.uniform(200, 600)),
        "power": round(random.uniform(200, 600)),
        "energy": round(random.uniform(200, 600))
    }
    print(Client.Publish(stateSensorTopic, json.dumps(payload)))
    time.sleep(5)
