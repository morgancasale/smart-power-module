import paho.mqtt.client as MQTT

class myMQTT():
    def __init__(self, clientID, broker, brokerPort, user, pwd, subNotifier = None):
        self.broker = broker
        self.brokerPort = brokerPort
        self.subNotifier = subNotifier

        self.isSub = False

        self.Client = MQTT.Client(clientID, True)
        self.Client.username_pw_set(user, pwd)
        
        self.Client.on_connect = self.OnConnect
        self.Client.on_message = self.OnMessageReceived


    def OnConnect(self, a, b, c, rc):
        print("Connected to %s with result code: %d" % (self.broker, rc))

    def OnMessageReceived(self, a, b, msg):
        self.subNotifier(msg.topic, msg.payload)

    def Publish(self, topic, payload, retain = False):
        print("Publishing at topic %s" % topic)
        self.Client.publish(topic, payload, 0, retain=retain)

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