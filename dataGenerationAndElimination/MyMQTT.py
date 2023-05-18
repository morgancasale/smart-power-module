import json
import paho.mqtt.client as mqtt
import app as app
import time
#"mqtt.eclipseprojects.io"

class MyMQTT:
    def __init__(self, cl, port, broker):
        self.client = mqtt.Client(cl, True)
        self.port = port
        self.broker = broker
        #self.notifier = notifier
        self.client.on_message = self.myOnMessageReceived
        self.client.on_connect = self.myOnConnect
        
    def on_message(self, client, userdata, message):
        print("Received message: {} on topic: {}".format(message.payload.decode(), message.topic))

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print("Connected to %s with result code: %d" % (self.broker, rc))

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        self.notifier.notify(msg.topic, msg.payload)
    
    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()


    def publish(self, topic, msg):
        self.client.publish(topic, msg)
        print('published on {}'.format(topic))

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_message(self, client, userdata, message):
        print("Topic: {}, Message: {}".format(message.topic, str(message.payload.decode())))

    def subscribe(self, topic):
        for top in topic:
            self.client.subscribe(top, 2)
            print("subscribed to %s" % (top))

'''class MyMQTT:
    def __init__(self,cl,port,broker):
        self.client = mqtt.Client(cl,True)
        self.port= port
        self.broker=broker

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def publish(self,topic,msg):    
            #msg= 'messaggio sul topic {}'.format(topic)
            self.client.publish(topic, msg)
            print('published on {}'.format(topic))

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_message(client, userdata, message):
        print("Topic: {}, Message: {}".format(message.topic, str(message.payload.decode())))

    def subscribe(self, topic):
        for top in topic:
            self.client.subscribe(top, 2)
            print("subscribed to %s" % (top))
'''
