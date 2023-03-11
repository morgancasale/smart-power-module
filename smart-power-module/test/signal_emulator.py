#PUBLISHER
from MyMQTT import *
import appliances as ap
import json
import time
import datetime as datetime
import numpy


class Emulator:
    def __init__(self, clientID, topic,broker,port):
        self.topic=topic
        self.client=MyMQTT(clientID,broker,port,None)
        self.message={'power':float, 'voltage':float, 'current':float, 'timestamp':''}
    

    def start (self):
        self.client.start()

    def stop (self):
        self.client.stop()


    def publish(self):
        app=ap.Appliances()
        message=self.message
        to_gen = 60
        power, voltage, current = app.standByPowerEmulator()
        #power, voltage, current= app.BlackoutBrownoutEmulator()
        for i in range(to_gen):
            p=power[i].tolist()
            v=voltage[i].tolist()
            c=current[i].tolist()
            
            time.sleep(2.0)
            message['power']=p
            message['voltage']=v
            message['current']=c
            message['timestamp']=str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
            print(message) 
        
            self.client.myPublish(self.topic,message)
        print("published")

if __name__ == "__main__":
    conf=json.load(open("settings.json"))
    broker=conf["broker"]
    port=conf["port"]
    signal_Emulator = Emulator("signal_emulator","IoT/miri/led",broker,port)
    signal_Emulator.client.start()
    time.sleep(2)
    print('This is a sensor emulator\n')
    done=False
    while not done:
        user_input = input('do you want to quit? \n') #y/n
        if user_input == 'n':
            signal_Emulator.publish()
        elif user_input=='y':
            done=True
        else:
            print('Unknown command')
    signal_Emulator.client.stop()  


