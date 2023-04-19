import os
import time
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

def REST_init(self):
    self.i = 5
    
def GET(self, *uri, **params):
    cmd = uri[0]
    a = params
    self.i+=1
    return json.dumps({"master" : False, "role" : self.i-1})

def notifier(topic, payload):
    data = json.loads(payload)
    print("Topic:"+ topic + ", The temperature is: " + str(data["temperature"]) + "°C")

if __name__ == "__main__":
    server = ServiceBase("test/deviceConnector.json", GET=GET, init_REST_func=REST_init, Notifier=notifier)
    server.start()
    clientErrorHandler = Client_Error_Handler()
    server.MQTT.subscribe("SmartSocket/temperature")

    while True:
        '''server.MQTT.publish("SmartSocket/cmd", {"state" : 1})
        time.sleep(5)
        server.MQTT.publish("SmartSocket/cmd", {"state" : 0})'''
        pass
        time.sleep(100)