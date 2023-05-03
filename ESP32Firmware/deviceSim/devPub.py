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

#discoveryTopic = "homeassistant/sensor/test/dev1/config"

pubTopic = "homeassistant/sensor/test/dev1/state"

availableTopic = "homeassistant/sensor/test/dev1/status"

'''regPayload = {
    "name": "dev1",
    "state_topic": pubTopic,
    "unit_of_measurement": "W",
    "value_template": "{{ value_json.power|default(0) }}",
    "availability_topic": availableTopic,
    "payload_available": "online",
    "payload_not_available": "offline"
}'''

#print(Client.Publish(discoveryTopic, json.dumps(regPayload)))

while(True):
    print(Client.Publish(availableTopic, "online"))
    print(Client.Publish(pubTopic, json.dumps({"power": round(random.uniform(200, 600))})))
    time.sleep(5)