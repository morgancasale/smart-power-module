#PUBLISHER
from app import *
import time
import datetime as datetime
import threading
import time
import sys

IN_DOCKER = os.environ.get("IN_DOCKER", False)
if not IN_DOCKER:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.append(PROJECT_ROOT)
from microserviceBase.serviceBase import *


class Emulator:
    def __init__(self):
        try:
            self.configFile_loc = "modulesEmulator.json"
            if(not IN_DOCKER):
                self.configFile_loc = "modulesEmulator/" + self.configFile_loc
            self.client = ServiceBase(self.configFile_loc)
            self.appClient = Appliances()

            self.client.start()

            self.deviceReg()
            i=0
            while (i<3):
                self.publishApp('normal')
                time.sleep(2)
                i+=1
        except HTTPError as e:
            message = "An error occurred while running the service: " + str(e._message)
            raise Exception(message)
        except Exception as e:
            message = "An error occurred while running the service: " + str(e)
            raise Exception(message)
        


    #modes: standbypower, faulty, blackout,maxpower, contatore, normal
    def messageGenerator(self,mode,dev):
        msg=None
        if mode == 'standbypower':
            msg=self.appClient.standByPowerEmulator(dev)
        else:
            msg=self.appClient.ApplianceEmulator(dev, mode)
        return msg

    def deviceReg(self):
        reg_info_file = "registration.json"
        if(not IN_DOCKER):
            reg_info_file = "dataGenerationAndElimination/" + reg_info_file
        data_reg = json.load(open(reg_info_file))

        catalog_address = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
        catalog_port = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
        
        url="http://%s:%s/getInfo"%(catalog_address, str(catalog_port))
        params={
            "table" : "EndPoints",
            "keyName" : "endPointName",
            "keyValue" : "deviceConnector"
        }  
        response = requests.get(url, params=params)
        endpoint = json.loads(response.text)
        ip_address = endpoint['IPAddress']
        port = endpoint['port']

        url_dc = "http://" + str(ip_address)+ ":" + str(port) + "/getRole"
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
        topic = "/smartSocket/data"
        for i in range(11):            
            msg=self.messageGenerator(mode, i)
            thread = threading.Thread(target=self.client.MQTT.Publish, args=(topic,msg))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
                
if __name__ == "__main__": 
    sensor = Emulator()
    #esp32firmware, true autobroker
    #request. get dev conn
    #res catalogue endpoint
            
    #for i sensori
    #esp32firmware, true autobroker
    #reqres catalogue endpoint
    #MAC su json, RSSI, autobroker, come parametri con ? '''

