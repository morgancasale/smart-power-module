import json
from .Error_Handler import *
import time
import paho.mqtt.client as MQTT
import requests

from threading import Thread, Event, current_thread

class MQTTServer(Thread):
    def __init__(self, threadID, threadName, events, configs,generalConfigs,configs_file, init_func=None, Notifier=None):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        self.events = events

        self.configParams = sorted([
            "endPointID", "endPointName", "autoBroker",
            "brokerAddress", "brokerPort", "subPub",
            "clientID", "MQTTTopics", "QOS"
        ])

        self.connected = False
        self.SubPub = ["sub", "pub"]
        self.isSub = False

        try:
            self.configs = configs
            self.generalConfigs = generalConfigs
            self.configs_file = configs_file
            self.clientErrorHandler = Client_Error_Handler()
            self.serverErrorHandler = Server_Error_Handler()

            if (self.check_and_loadConfigs()):
                if (self.configs["autoBroker"]): # sse personalizzo prendo broker da config, senno da resource catalogue                    
                    broker_AddPort = self.getMQTTBroker()

                    self.broker = broker_AddPort["IPAddress"]
                    self.brokerPort = broker_AddPort["port"]
                    if (self.broker == None or self.brokerPort == None):
                        raise self.clientErrorHandler.BadRequest("Missing broker address or port in Resource Catalogue")
                    
                    if(self.generalConfigs["MQTT"]["brokerAddress"] == None or self.generalConfigs["MQTT"]["brokerPort"] == None):
                          self.updateConfigFile( {"brokerAddress": self.broker, "brokerPort": self.brokerPort})

                self.subNotifier = Notifier

                self.MQTTSubTopic =  [(topic, self.QOS)  for topic in self.configs["MQTTTopics"]["sub"]]

            if (init_func != None): init_func()

            self.Client = MQTT.Client(self.clientID, True)

            self.Client.on_connect = self.OnConnect
            self.Client.on_message = self.OnMessageReceived

        except HTTPError as e:
            self.events["stopEvent"].set()
            raise HTTPError( status=e.status, message = "An error occurred while enabling the MQTT server: \u0085\u0009" + e._message)
        except Exception as e:
            self.events["stopEvent"].set()
            raise self.serverErrorHandler.InternalServerError(
                "An error occurred while enabling MQTT server: \u0085\u0009" + str(e)
            )

    def openMQTTServer(self):
        self.Client.connect(self.broker, self.brokerPort)

        self.Client.loop_start()
        self.events["stopEvent"].wait()
        self.stop()

    def run(self):
        try:
            print("MQTT - Thread %s waiting for registration..." % current_thread().ident)
            self.events["startEvent"].wait()
            self.openMQTTServer()
            


        except HTTPError as e:
            self.events["stopEvent"].set()
            raise HTTPError( status=e.status, message = "An error occurred while running the MQTT server: \u0085\u0009" + e._message)
        except Exception as e:
            self.events["stopEvent"].set()
            raise self.serverErrorHandler.InternalServerError(
                "An error occurred while running the MQTT server: \u0085\u0009" + str(e)
            )

    def OnConnect(self, a, b, c, rc):
        print("Connected to %s with result code: %d" % (self.broker, rc))
        if(rc == 0):
            self.connected = True
        else:
                raise self.serverErrorHandler.InternalServerError(
                "no conncetion to broker"
            )

    def OnMessageReceived(self, a, b, msg):
        self.subNotifier(msg.topic, msg.payload)

    def Publish(self, topics, msg):
        while(not self.connected):
            time.sleep(5)
        if(not isinstance(topics, list)):
            topics = [topics]
        if (self.configs["subPub"]["pub"]):
            for topic in topics:
                self.checkTopic(topic, "pub")

                print("Publishing '%s' at topic '%s'" % (msg, topic))
                self.Client.publish(topic, json.dumps(msg), 2)
        else:
            raise self.clientErrorHandler.BadRequest(
            "Publisher is not active for this service")


    def Subscribe(self, topics):
        while(not self.connected):
            time.sleep(5)
        if(not isinstance(topics, list)):
            topics = [topics]
        if (self.configs["subPub"]["sub"]):
            if (len(topics) >1):
                MQTTTopics = []
            self.topics = []
            for topic in topics:
                self.checkTopic(topic,"sub")
                if (len(topics) ==1):
                        MQTTTopics = (topic, 2)
                        self.topics = topic
                else:
                        MQTTTopics.append((topic, 2))
                        self.topics.append(topic)
            print("subscribing '%d' at topic '%s'" % (2,   MQTTTopics ))
            self.Client.subscribe(MQTTTopics)
            self.isSub = True

        else:
            raise self.clientErrorHandler.BadRequest("Error subscriber not activated")

    def Unsubscribe(self):
        if (self.isSub):
            self.Client.unsubscribe(self.topics)

    def stop(self):
        self.connected = False
        self.Unsubscribe()

        self.Client.loop_stop()
        self.Client.disconnect()



    def updateConfigFile(self, dict):
        try:

            self.generalConfigs["MQTT"]["brokerAddress"] = dict["brokerAddress"]
            self.generalConfigs["MQTT"]["brokerPort"] = dict["brokerPort"]
            

            with open(self.configs_file, 'w') as file:
                 json.dump(self.generalConfigs, file, indent=4)
            # with open(self.configs_file, "w") as file:
            #     json.dump(configs, file, indent=4)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(
                "An error occurred while updating the configuration file: \u0085\u0009" + str(e)
            )
        
    def getMQTTBroker(self):
        try:
            url = self.generalConfigs["REGISTRATION"]["catalogAddress"] + ":"
            url += str(self.generalConfigs["REGISTRATION"]["catalogPort"])+ "/getInfo"
            params = {
                "table": "EndPoints",
                "keyName": "endPointName",
                "keyValue": "MQTTBroker"
            }

            response = requests.get(url, params=params)
            if(response.status_code != 200):
                raise HTTPError(response.status_code, str(response.text))
            
            return response.json()[0]
        except HTTPError as e:
            raise self.clientErrorHandler.BadRequest("An error occurred while getting MQTT broker: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError("An error occurred while getting MQTT broker: \u0085\u0009" + str(e))

    def Wildcards(self,topic, subpub):

        topic = topic.split("/")
        hash_find = [i for i, x in enumerate(topic) if x == "#"]
        plus_find = [i for i, x in enumerate(topic) if x == "+"]
        subtopic = []

        if(hash_find != []):

            if (len(hash_find) > 1):
                raise self.clientErrorHandler.BadRequest("Error # wildcard can't be more than one")

            if (len(plus_find) < 1):
                subtopic.extend(topic[0:hash_find[0]])

            else:
                if (plus_find[-1] > hash_find[0]):
                    raise self.clientErrorHandler.BadRequest("Error + wildcard can't be before #")
                temp = 0
                for i in range(len(plus_find)):
                    subtopic.extend(topic[temp:plus_find[i]-1])
                    temp = plus_find[i]+1
                if (hash_find > 0):
                    subtopic.extend(topic[temp:hash_find[0]]  )
                else:
                    subtopic.extend(topic[temp:])
        elif (plus_find != []):
            temp = 0
            for i in range(len(plus_find)):
                subtopic.extend(topic[temp:plus_find[i]-1])
                temp = plus_find[i]+1
            subtopic.extend(topic[temp:])
        listTopic = []


        for i in range(len(self.configs["MQTTTopics"][subpub])):
            singleTopic = []

            if (len(plus_find) == 0):

                 singleTopic.extend(self.configs["MQTTTopics"][subpub][i].split("/")[0:hash_find[0]])
            else:
                temp = 0
                for j in range(len(plus_find)):
                    singleTopic.extend(self.configs["MQTTTopics"][subpub][i].split("/")[temp:plus_find[j]-1])
                    temp = plus_find[j]+1

                if (hash_find != []):
                    singleTopic.extend(self.configs["MQTTTopics"][subpub][i].split("/")[temp:hash_find[0]])
                else:
                    singleTopic.extend(self.configs["MQTTTopics"][subpub][i].split("/")[temp:])

            listTopic.append(singleTopic)

        if( subtopic in listTopic):
            return True
        else:
            raise self.clientErrorHandler.BadRequest("Error topic not in config file")


    def checkTopic(self,topic, subpub):
        if ("+" not in topic and "#" not in topic):
            if ( topic  not in self.configs["MQTTTopics"][subpub]):
                raise self.clientErrorHandler.BadRequest("Error topic not in config file")

        else:
           self.Wildcards(topic, subpub)
        return True


    def changeSubTopic(self, newtopic):
        if (self.configs["subPub"]["sub"]):
            self.Unsubscribe()
            for topic in newtopic:
               self.checkTopic(topic,"sub")
               self.Subscribe(newtopic)
        else:
            raise self.clientErrorHandler.BadRequest("Error subscriber not activated")

    def checkParams(self):
        if (not self.configParams == sorted(self.configs.keys())):
            raise self.clientErrorHandler.BadRequest(
                "Missing parameters in config file")

        if(not all(key in self.SubPub  for key in self.configs["subPub"].keys())):
            raise self.clientErrorHandler.BadRequest(
                "Missing parameters in config file")

        if(not all(key in self.SubPub  for key in self.configs["MQTTTopics"].keys())):
            raise self.clientErrorHandler.BadRequest(
                "Missing parameters in config file")

    def validateParams(self):
        if (not isinstance(self.configs["endPointName"], str)):
            raise self.clientErrorHandler.BadRequest(
                "endPointName parameter must be a string")
        self.endPointName = self.configs["endPointName"]

        if (not isinstance(self.configs["endPointID"], str)):
            raise self.clientErrorHandler.BadRequest(
                "endPointID parameter must be a string")
        self.endPointID = self.configs["endPointName"]

        if (not isinstance(self.configs["autoBroker"], bool)):
            raise self.clientErrorHandler.BadRequest(
                "autoBroker parameter must be a boolean")

        if(not self.configs["autoBroker"]):
            if (not isinstance(self.configs["brokerAddress"], str)):
                raise self.clientErrorHandler.BadRequest(
                    "brokerAddress parameter must be a string")
            self.broker = self.configs["brokerAddress"]

            if (not isinstance(self.configs["brokerPort"], int)):
                raise self.clientErrorHandler.BadRequest(
                    "brokerPort parameter must be a int")
            self.brokerPort = self.configs["brokerPort"]

        if(not isinstance(self.configs["subPub"], dict)):
            raise self.clientErrorHandler.BadRequest(
                "subPub parameter must be a dict")

        if(not isinstance(self.configs["MQTTTopics"], dict)):
            raise self.clientErrorHandler.BadRequest(
                "subPub parameter must be a dict")

        for method in self.SubPub:
            if (not isinstance(self.configs["subPub"][method], bool)):
                raise self.clientErrorHandler.BadRequest(
                    method + " parameter must be a boolean")

        for method in self.SubPub:
            if (not isinstance(self.configs["MQTTTopics"][method], list)):
                raise self.clientErrorHandler.BadRequest(
                    method + " parameter must be a list")
            for topic in self.configs["MQTTTopics"][method]:
                if (not isinstance(topic, str)):
                    raise self.clientErrorHandler.BadRequest(
                        method + " parameter must be a list of strings")

        self.subTopics = self.configs["MQTTTopics"]["sub"]
        self.pubTopis = self.configs["MQTTTopics"]["pub"]

        if (not isinstance(self.configs["clientID"], str)):
            raise self.clientErrorHandler.BadRequest(
                "clientID parameter must be a string")
        self.clientID = self.configs["clientID"]
        if (not isinstance(self.configs["QOS"], int)):
            raise self.clientErrorHandler.BadRequest(
                "QOS parameter must be a int")
        self.QOS = self.configs["QOS"]


    def check_and_loadConfigs(self):
        try:
            self.checkParams()
            self.validateParams()
            return True
        except HTTPError as e:
            raise HTTPError( status=e.status, message = "MQTT configs have errors: \u0085\u0009" + e._message)
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(
                "MQTT configs have errors: \u0085\u0009" + str(e)
            )