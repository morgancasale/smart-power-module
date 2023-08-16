#PUBLISHER
from app import *
import json
import time
import datetime as datetime
import threading
import os
import time
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(PROJECT_ROOT)
from microserviceBase.serviceBase import *


class Emulator:
    def __init__(self):
        self.client= ServiceBase("C:/Users/mirip/Desktop/progetto_IOT/smart-power-module/standByPowerDetection/serviceConfig_example.json")
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
        topic="?/smartSocket/data"
        self.client.start()
        for i in range(11):
            #get
            msg=self.messageGenerator(mode, i)
            thread = threading.Thread(target=self.client.MQTT.Publish, args=(topic,msg))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()


                
if __name__ == "__main__":
    sensor=Emulator()
    #sensor.publishApp('standbypower')
    sensor.publishApp('normal')
    
    #esp32firmware, true autobroker
    #request. get dev conn
    #res catalogue endpoint
            
    #for i sensori
    #esp32firmware, true autobroker
    #reqres catalogue endpoint
    #MAC su json, RSSI, autobroker, come parametri con ?

