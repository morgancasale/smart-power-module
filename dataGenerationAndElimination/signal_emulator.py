#PUBLISHER 127.0.0.1 192.168.2.145
from app import *
import json
import time
import datetime as datetime
import threading
import os
import time
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)

from microserviceBase.serviceBase import *

class Emulator:
    def __init__(self):
        self.threads = [] 
        self.running=0
        try:
            config_file = "emulatorConfig.json"
            if(not IN_DOCKER):
                config_file = "dataGenerationAndElimination/" + config_file
        
            self.client= ServiceBase("C:/Users/mirip/Desktop/progetto_IOT/smart-power-module/dataGenerationAndElimination/dataGen.json")
            self.appClient=Appliances()
            i=0
            while(i<=60): 
                self.deviceReg()
                self.publishApp('normal')
                self.joinThreads()  # Start the threads
                i+=1
        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise Exception(message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Exception(message)

    #modes: standbypower, faulty, blackout,maxpower, contatore, normal
    def messageGenerator(self,mode,dev):
        if mode == 'standbypower':
            msg=self.appClient.standByPowerEmulator(dev)
        else:
            msg=self.appClient.ApplianceEmulator(dev, mode)
        return msg

    def deviceReg(self):

        json_data = json.load(open('dataGenerationAndElimination/dataGen.json'))
        data_reg=data =json.load(open('dataGenerationAndElimination/registration.json'))
        catalog_address = json_data["REGISTRATION"]["catalogAddress"]
        catalog_port = json_data["REGISTRATION"]["catalogPort"]
        
        url="%s:%s/getInfo"%(catalog_address, str(catalog_port))
        params={
        "table" : "EndPoints",
        "keyName" : "endPointName",
        "keyValue" : "deviceConnector"
        }  
        response = requests.get(url, params=params)
        response = response.json()[0]
        endpoint = response
        port = endpoint.get('port')

        url_dc=  str(catalog_address)+ ":" + str(port) + "/getRole"
        for entry in data_reg["entries"]:
            mac = entry["MAC"]
            auto_broker = entry["autoBroker"]
            auto_topics = entry["autoTopics"]
            params_dc={
                        "MAC": mac,
                        "autoBroker": auto_broker,
                        "autoTopics": auto_topics
            }  
            requests.get(url_dc, params=params_dc)

    #modes: faulty o blackout
    #faulty : range simulazione vengono presi da faulty_simualtion.json
    #non vanno tv e washing machine (modulo 1 e 2)
    #blackout: 5 elettrodmestici con misurazione di tensione anomale
    #maxpower : D11 (heater) supera maxpower
    #contatore: potenza supera quella massima supportata dal contatore
    #normal : funziona senza problemi
    #standbypower
    def publishApp(self, mode):
        self.client.start()
        for i in range(11):
            thread = threading.Thread(target=self.deviceSim, args=(mode, i))
            self.threads.append(thread)
            
    def deviceSim(self, mode, i):
        topic = "/smartSocket/data"
        msg=self.messageGenerator(mode, i)
        self.client.MQTT.Publish(topic,msg)
        time.sleep(2)
    
    def joinThreads(self):
        for thread in self.threads:
            if not self.running:#not thread.is_alive():  # Start only if the thread is not already running
                thread.start()
        self.running=1        

    
if __name__ == "__main__":
    Emulator()