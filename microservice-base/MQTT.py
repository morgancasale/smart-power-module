import json
import Error_Handler
import time
import paho.mqtt.client as MQTT


class MyMQTT():
    def __init__(self, clientID, broker, brokerPort, subNotifier=None):
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
        if (self.isSub):
            self.Client.unsubscribe(self.topic)

    def stop(self):
        if (self.isSub):
            self.unsubscribe

            self.Client.loop_stop()
            self.Client.disconnect()


class MQTTServer(object):

    def __init__(self, config_file, init_func=None, Notifier=None, SubTopics=None):

        
        self.SubPub = ["sub", "pub"]
        try:
            self.errorHandler = Error_Handler()
            self.config_file = config_file

            if (self.check_and_loadConfigs()):
                self.broker = self.configs["Broker_Address"]
                self.brokerPort = self.configs["Broker_Port"]
                self.clientID = self.configs["Client_ID"]
                self.notify = Notifier
                self.Qos = self.configs["QoS"]

                if (self.configs["Active"]):

                    self.Client = MyMQTT(
                        self.clientID, self.broker, self.brokerPort, subNotifier=self.notify)
                    self.Client.start()
                    time.sleep(3)
                    if (self.configs["SubPub"]["sub"]):
                        for sub in SubTopics:
                            self.Client.Subscribe(sub)
                    if (not self.configs["SubPub"]["pub"]):
                        self.publish = self.publish_error()

            init_func()

        except Exception as e:
            print(e)

    def publish(self, topic, msg):
        self.Client.Publish(topic, msg)

    def publish_error(self):
        raise self.Error_Handler.functionError(
            "Publisehr is not active for this service")

    def checkParams(self):
        config_params = ["active", "Broker_Address", "SubPub",
                         "Client_ID", "Broker_Port", "Sub_Topic", "Pub_Topic", "QoS"]

        if (not all(key in config_params for key in self.configs.keys())):
            raise self.errorHandler.MissingDataError(
                "Misssing parameters in config file")

        if (not any(key in config_params for key in self.configs["SubPub"].keys())):
            raise self.errorHandler.MissingDataError(
                "At least one Subscriber or Publisher method must be enabled")

    def validateParams(self):
        if (not isinstance(self.configs["active"], bool)):
            raise self.errorHandler.MissingDataError(
                "Active parameter must be a boolean")

        if (not isinstance(self.configs["Client_ID"], str)):
            raise self.errorHandler.MissingDataError(
                "Client_ID parameter must be a string")

        if (not isinstance(self.configs["Broker_Address"], str)):
            raise self.errorHandler.MissingDataError(
                "Broker_Address parameter must be a string")

        if (not isinstance(self.configs["Broker_Port"], int)):
            raise self.errorHandler.MissingDataError(
                "Broker_Port parameter must be a int")

        if (not isinstance(self.configs["QoS"], int)):
            raise self.errorHandler.MissingDataError(
                "QoS parameter must be a int")

        for method in self.SubPub:
            if (method in self.configs["SubPub"].keys()):
                if (not isinstance(self.configs["SubPub"][method], bool)):
                    raise self.errorHandler.MissingDataError(
                        method + " parameter must be a boolean")

    # TODO chek if file exists, check if all needed configs are there
    def check_and_loadConfigs(self):

        try:
            configs = json.load(open(self.config_file, 'r'))

            self.configs = configs["MQTT"]
            self.checkParams()
            self.validateParams()
            return True

        except Exception as e:
            print(e)
   

    def openRESTServer(s):
        