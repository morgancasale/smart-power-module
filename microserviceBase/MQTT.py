import json
from .Error_Handler import *
import time
import paho.mqtt.client as MQTT
import requests
import os
import dns.resolver

from threading import Thread, Event, current_thread

IN_DOCKER = os.environ.get("IN_DOCKER", False)

class MQTTServer(Thread):
    def __init__(self, threadID, threadName, events, configs, generalConfigs, configs_file, init_func=None, Notifier=None):
        Thread.__init__(self)
        self.threadID = threadID
        self.name = threadName
        self.events = events

        self.configParams = sorted([
            "endPointID", "endPointName", "autoBroker",
            "brokerAddress", "brokerPort", "subPub",
            "clientID", "MQTTTopics", "QOS","username","password"
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

                url = self.generalConfigs["REGISTRATION"]["catalogAddress"] + ":"
                url += str(self.generalConfigs["REGISTRATION"]["catalogPort"])+ "/getInfo"
                params = {
                    "table": "EndPoints",
                    "keyName": "endPointName",
                    "keyValue": "MQTTBroker"
                }


                if (self.configs["autoBroker"]): # sse personalizzo prendo broker da config, senno da resource catalogue
                    response= requests.get(url, params=params)
                    if(response.status_code != 200):
                        raise HTTPError(response.status_code, str(response.text))


                    broker_AddPort = response.json()[0]
                    
                    if(not IN_DOCKER):
                        self.broker = broker_AddPort["IPAddress"]
                    
                        if(self.generalConfigs["REGISTRATION"]["catalog_mDNS"] != None):
                            loc = os.path.dirname(__file__) + "/../general.json"
                            system_mDNS = json.load(open(loc, 'r'))["hostname"]+".local"
                            self.broker = self.resolvemDNS(system_mDNS)
                    else:
                        self.broker = "172.20.0.10"
                    self.brokerPort = broker_AddPort["port"]
                    self.username = broker_AddPort["MQTTUser"]
                    self.password = broker_AddPort["MQTTPassword"]
                    if (self.broker == None or self.brokerPort == None):
                        raise self.clientErrorHandler.BadRequest("Missing broker address or port in Resource Catalogue")
                    if (self.username == None or self.password == None):
                        raise self.clientErrorHandler.BadRequest("Missing broker username or password in Resource Catalogue")
                    
                    if(self.generalConfigs["MQTT"]["brokerAddress"] == None or self.generalConfigs["MQTT"]["brokerPort"] == None):
                          self.updateConfigFile( {"brokerAddress": self.broker, "brokerPort": self.brokerPort})
                    if(self.generalConfigs["MQTT"]["username"] == None or self.generalConfigs["MQTT"]["password"] == None):
                          self.updateConfigFile( {"username": self.username, "password": self.password})

                self.subNotifier = Notifier

                self.MQTTSubTopic =  [(topic, self.QOS)  for topic in self.configs["MQTTTopics"]["sub"]]

            if (init_func != None): init_func()

            self.Client = MQTT.Client(self.clientID, True)

            self.Client.on_connect = self.OnConnect
            self.Client.on_disconnect = self.OnDisconnect
            #self.Client.on_message = self.OnMessageReceived

        except HTTPError as e:
            self.events["stopEvent"].set()
            raise HTTPError( status=e.status, message = "An error occurred while enabling the MQTT server: \u0085\u0009" + e._message)
        except Exception as e:
            self.events["stopEvent"].set()
            raise self.serverErrorHandler.InternalServerError(
                "An error occurred while enabling MQTT server: \u0085\u0009" + str(e)
            )

    def openMQTTServer(self):
        self.Client.username_pw_set(username=self.username, password=self.password)
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
        threadName = current_thread().getName()
        print("Thread %s connected to %s with result code: %d" % (threadName, self.broker, rc))
        print()
        if(rc == 0):
            self.connected = True
        else:
            raise self.serverErrorHandler.InternalServerError(
                "No connection to broker"
            )
        
    def OnDisconnect(self, client, userdata, rc):
        print("Disconnection reason " + str(rc))
        self.connected = False

    def OnMessageReceived(self, a, b, message):
        self.subNotifier(self, message.topic, message.payload)

    def Publish(self, topics, message, retain=False, talk = True):
        while(not self.connected):
            time.sleep(5)
        if(not isinstance(topics, list)):
            topics = [topics]
        if (self.configs["subPub"]["pub"]):
            for topic in topics:
                self.checkTopic(topic, "pub")
                if(len(self.publishtopics)>1):
                    for publishtopic in  self.publishtopics:
                        if(talk): print("Publishing '%s' at topic '%s'" % (message, publishtopic))
                        self.Client.publish(publishtopic, message, self.QOS, retain=retain)
                else:
                    if(talk): print("Publishing '%s' at topic '%s'" % (message, topic))
                    self.Client.publish(topic, message, self.QOS, retain=retain)
        else:
            raise self.clientErrorHandler.BadRequest(
            "Publisher is not active for this service")


    def Subscribe(self, topics, callback = None):
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
                
                if(callback is None):
                    self.Client.message_callback_add(topic, self.OnMessageReceived)
                else:
                    self.Client.message_callback_add(topic, callback)
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

    def notifyHA(self, msg, talk=False):
        topic = "socket_settings/notifier"
        msg = json.dumps(msg)
        self.Publish(topic, msg, talk = talk)

    def resolvemDNS(self, mDNS):
        try:
            if(os.name != None):
                resolver = dns.resolver.Resolver()
                resolver.nameservers = ["224.0.0.251"]
                resolver.port = 5353
                sol = resolver.resolve(mDNS, "A")
                return str(sol[0].to_text())
            else:
                PORT = 50000
                MAGIC = "smartSocket" #to make sure we don't confuse or get confused by other programs
                from socket import socket, AF_INET, SOCK_DGRAM

                s = socket(AF_INET, SOCK_DGRAM) #create UDP socket
                s.bind(('', PORT))
                data, addr = s.recvfrom(1024) #wait for a packet
                if data.startswith(MAGIC.encode()):
                    IP = data[len(MAGIC):].decode()
                    print ("got service announcement from %s", IP)

                return IP
        except Exception as e:
            raise self.serverErrorHandler.InternalServerError(message="An error occurred while resolving mDNS: \u0085\u0009" + str(e))
    
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

    def Wildcards(self,topic, subpub):
        self.publishtopics = []
        Topic = topic
        topic = topic.split("/")
        hash_find = [i for i, x in enumerate(topic) if x == "#"]
        plus_find = [i for i, x in enumerate(topic) if x == "+"]
        subtopic = []
        if("#" in char for char in self.configs["MQTTTopics"][subpub]):
             hash_topics = []
             hash_input_topic = []
             for topics in self.configs["MQTTTopics"][subpub]:
                 if("#" in topics):
                     hash_find_topics = [i for i, x in enumerate(topics.split("/")) if x == "#"]
                     hash_topics.append(topics.split("/")[:hash_find_topics[0]])
                     hash_input_topic.append(topic[:hash_find_topics[0]])
             for i in range(len(hash_input_topic)):
                if(hash_input_topic[i] in hash_topics):
                    self.publishtopics.append(Topic)
                    return True    
        else:

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
                if(subpub == "pub"):
                    indexpub =  [i for i, x in enumerate(listTopic) if x == subtopic]
                    for j in indexpub:
                        self.publishtopics.append(self.configs["MQTTTopics"][subpub][j])
                return True
            else:
                raise self.clientErrorHandler.BadRequest("Error topic not in config file")


    def checkTopic(self,topic, subpub):
        if(subpub == "sub"):   
            if ("+" not in topic and "#" not in topic ):
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
        if (not sorted(self.configParams) == sorted(self.configs.keys())):
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
     

        if(not self.configs["username"]):
            if (not isinstance(self.configs["username"], str)):
                raise self.clientErrorHandler.BadRequest(
                    "username parameter must be a string")
       
        

        if(not self.configs["password"]):
            if (not isinstance(self.configs["password"], str)):
                raise self.clientErrorHandler.BadRequest(
                    "password parameter must be a string")
        if(not self.configs["autoBroker"]):
            self.broker = self.configs["brokerAddress"]
            self.username = self.configs["username"]    
            self.password = self.configs["password"]
            self.brokerPort = self.configs["brokerPort"]    

        if (not isinstance(self.configs["brokerPort"], int)):
                raise self.clientErrorHandler.BadRequest(
                    "brokerPort parameter must be a int")
        

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