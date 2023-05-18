#PUBLISHER
from MyMQTT import *
from app import *
import json
import time
import datetime as datetime
import threading
import re


class Emulator:
    def __init__(self):
     
        #self.broker="mqtt.eclipseprojects.io"
        self.broker="broker.emqx.io"
        self.clientID='shdgfdhjnfbghn'
        self.port=1883
        self.client= 'smartmoduleclientprova11'
        self.client=MyMQTT(self.client, self.port, self.broker )
        conf_t=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/topic.json'))
        self.topics=conf_t["topics"]
        self.appClient=Appliances()

        self.client.start()

    #modes: standbypower, faulty, blackout,maxpower, contatore, normal
    def messageGenerator(self,mode,dev):
        msg=None
        if mode == 'standbypower':
            msg=self.appClient.standByPowerEmulator(dev)
        else:
            msg=self.appClient.ApplianceEmulator(dev, mode)
        return msg


    #modes:standbypower faulty, blackout 
    def publishApp(self,mode):
  
        threads = []
        for topic in self.topics:
            parts = topic.split("/")
            dev = parts[-1]
            msg=self.messageGenerator(mode, dev)
            thread = threading.Thread(target=self.client.publish, args=(topic,msg))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

                
if __name__ == "__main__":
    sensor=Emulator()
    #sensor.publishApp('standbypower')
    sensor.publishApp('normal')

