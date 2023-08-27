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
        self.client= ServiceBase("C:/Users/mirip/Desktop/progetto_IOT/smart-power-module/dataGenerationAndElimination/res_catalog_serviceConfig.json")
        self.appClient=Appliances()

    #modes: standbypower, faulty, blackout,maxpower, contatore, normal
    def messageGenerator(self,mode,dev):
        msg=None
        if mode == 'standbypower':
            msg=self.appClient.standByPowerEmulator(dev)
        else:
            msg=self.appClient.ApplianceEmulator(dev, mode)
        return msg

    def deviceReg(self):
        json_data = json.load(open('dataGenerationAndElimination/res_catalog_serviceConfig.json'))
        data_reg=data =json.load(open('dataGenerationAndElimination/registration.json'))
        catalog_address = json_data['REST']['IPAddress']
        catalog_port = json_data['REST']['port']
        
        url="http://%s:%s/getInfo"%(catalog_address, str(catalog_port))
        params={
        "table" : "EndPoints",
        "keyName" : "endPointName",
        "keyValue" : "deviceConnector"
        }  
        response = requests.get(url, params=params)
        response = response.json()[0]
        endpoint = response
        ip_address = endpoint.get('IPAddress')
        port = endpoint.get('port')

        url_dc= "http://" + str(ip_address)+ ":" + str(port) + "/getRole"
        for entry in data_reg['entries']:
            mac = entry['MAC']
            auto_broker = entry['autoBroker']
            auto_topics = entry['autoTopics']
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
    def publishApp(self,mode):
        threads = []
        topic="/smartSocket/data"
        self.client.start()
        for i in range(11):
            
            msg=self.messageGenerator(mode, i)
            thread = threading.Thread(target=self.client.MQTT.Publish, args=(topic,msg))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
                
if __name__ == "__main__": 
    sensor=Emulator()
    sensor.deviceReg()
    i=0
    while (i<3):
        sensor.publishApp('normal')
        time.sleep(2)
        i+=1
    #esp32firmware, true autobroker
    #request. get dev conn
    #res catalogue endpoint
            
    #for i sensori
    #esp32firmware, true autobroker
    #reqres catalogue endpoint
    #MAC su json, RSSI, autobroker, come parametri con ? '''

