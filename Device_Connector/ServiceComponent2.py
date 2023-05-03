from ESP_Agent import *
from MyMQTT import *
from customErrors import *
import requests

class Sensor:
    #1: inizializzo e faccio subscription
    def __init__(self):
        self.broker = "broker.emqx.io"
        self.brokerPort = 1883
        
        self.clientID = "Sensor"
        self.runChrono = False

        self.Client = MyMQTT(self.clientID, self.broker, self.brokerPort, subNotifier = self.notify)
        
        self.Client.start()
        time.sleep(3)
        self.Client.Subscribe("/command/#")
         
#2. controllo il topic, se buono allora mando il comando
    def notify(self, topic, payload):
        try:
            self.checkTopic(topic)
            self.sendComand(self.topic[3], self.topic[4])
        except web_exception as e:
            raise web_exception(400, "Error in notify: " + e.message)
        
#2.B get request per avere lista di ID
    def AvailableDevices(self):
        url = "http://localhost:8080/getInfo?table=Devices&keyName=Online&keyValue=1"
        self.getResponseDev = requests.get(url)

#2.A controllo tutte e voci deltopic se in linea con switch, numero e comando
    def checkTopic(self,topic):
        self.AvailableDevices()
        self.topic = topic.split("/")
        if self.topic[1] not in self.getResponseDev["DeviceID"] :
            raise web_exception(400, "No Device Available")
        if self.topic[2].lower() != "switch":
            raise web_exception(400, "Incorrect Request")   
        if  self.topic[3] not in [1,2,3]:
            raise web_exception(400, "Incorrect switch number")
        if self.topic[4].lower() not in ["on", "off"]:
            raise web_exception(400, "Incorrect command")
#2.B CREATE COMMAND
    def createCommand(self):
        self.Client.Publish("actuator/"+ self.topic[1] +"/switch/"+ self.topic[3], self.cmd)
    
 #2.C se topic giusto allora mando il comando all'actuator   
    def sendComand(self,number,command):
        if command.lower() == "on":
            self.cmd = 1
        else:
            self.cmd = 0    
       
        # mando su altro broker? o formatto sotto froma di json?
    
#3. mando i dati     
    def sendData(self):
        for i in self.data["deviceID"]:
            self.DeviceID = self.data["deviceID"][i]
            DataPassive = self.data["Data"]
            Data = DataPassive["Passive"]

            for (key, value) in Data:
             self.Client.Publish("data/"+ self.DeviceID+"/" + key ,value)    
           
               

 


#loop per dati
if __name__ == "__main__":
    sensor = Sensor()

    while(True):        
        sensor.sendData()
        time.sleep(5)
    
#IMPLEMENTAZIONE:
#1. togliere punlisher da notify 
#2. implentare modo di disconnettere serverè