import time
import random
import json
from MinMQTT import *

clientID = "test_sensor"
broker = "192.168.2.191"
brokerPort = 1883
user = "morgan"
pwd = "oppioppi"

set_topic = "/home/ts/set"
state_topic = "/home/tsens/state"

class Sensor:
    def __init__(self):
        self.Client = MinMQTT(clientID, broker, brokerPort, user, pwd, subNotifier=self.notify)
        self.Client.start()

        #self.Client.Subscribe(set_topic)
        while(True):
            self.publish()
            time.sleep(3)

    def notify(self, topic, msg):
        if(msg == b"ON"):
            print("Turning ON switch")
            self.Client.Publish(state_topic, "ON")
        elif(msg == b"OFF"):
            print("Turning OFF switch")
            self.Client.Publish(state_topic, "OFF")

    def publish(self):
        current = round(random.uniform(0, 10), 3)
        voltage = round(random.uniform(218, 222), 3)
        powerh = round(random.uniform(18, 24), 3)
        payload = {"current" : current, "voltage" : voltage, "power" : round(current * voltage, 3), "powerh" : powerh}
        # print("Publishing power value: " + str(payload["power"]) + "W")
        self.Client.Publish(state_topic, json.dumps(payload))

if __name__ == "__main__":
    switch = Sensor()