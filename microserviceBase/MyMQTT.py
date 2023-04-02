import json
import time
import paho.mqtt.client as MQTT
class MyMQTT():
    def __init__(self, clientID, broker, brokerPort, subNotifier = None):
        self.broker = broker
        self.brokerPort = brokerPort
        self.subNotifier = subNotifier

        self.isSub = False

        self.Client = MQTT.Client(clientID, True)
        
        self.Client.on_connect = self.OnConnect
        self.Client.on_message = self.OnMessageReceived

    def OnConnect(self, a, b, c, rc):
        print("Connected to %s with result code: %d" % (self.broker, rc))

    def OnMessageReceived(self, a, b, msg):
        self.subNotifier(msg.topic, msg.payload)

    def Publish(self, topic, msg):
        print("Publishing '%s' at topic '%s'" % (msg, topic))
        self.Client.publish(topic, json.dumps(msg), 2)

    def Subscribe(self, topic):
        self.Client.subscribe(topic, 2)
        self.isSub = True
        self.topic = topic

    def start(self):
        self.Client.connect(self.broker, self.brokerPort)
        self.Client.loop_start()

    def unsubscribe(self):
        if(self.isSub):
            self.Client.unsubscribe(self.topic)

    def stop(self):
        if(self.isSub):
            self.unsubscribe

            self.Client.loop_stop()
            self.Client.disconnect()