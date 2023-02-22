import time
from MinMQTT import *

clientID = "test_switch"
broker = "192.168.2.191"
brokerPort = 1883
user = "morgan"
pwd = "oppioppi"

set_topic = "/home/ts/set"
state_topic = "/home/ts"

class Switch:
    def __init__(self):
        self.Client = MinMQTT(clientID, broker, brokerPort, user, pwd, subNotifier=self.notify)
        self.Client.start()

        time.sleep(3)

        self.Client.Subscribe(set_topic)

    def notify(self, topic, msg):
        if(msg == b"ON"):
            print("Turning ON switch")
            self.Client.Publish(state_topic, "ON")
        elif(msg == b"OFF"):
            print("Turning OFF switch")
            self.Client.Publish(state_topic, "OFF")

if __name__ == "__main__":
    switch = Switch()
    while True:
        time.sleep(1)