import numpy as np
import matplotlib.pyplot as plt
import json
import re

class Appliances():
    def __init__(self) :
        conf_t=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/faultyAppBlackout.json'))
        self.ranges=conf_t["smartModule"]
        self.faulty=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/faulty_simulation.json'))
        self.blackout=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/blackout_simulation.json'))
        self.maxPower=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/maxPower.json'))
        self.contatore=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/contatore.json'))
        self.normal=json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/normalFunctioning.json'))

    def standByPowerEmulator(self,devID): #possono avere tutti stesso perchè range molto simile
        
        digits = re.findall(r'\d+', devID)
        ID_num = ''.join(digits)
        ID= 'D' + str(ID_num)
        power=np.random.randint(1,5, 1)
        voltage= 230
        current= power/voltage
        data = ( {
        'DeviceID': ID,
        'Voltage': voltage,
        'Current': current[0],
        'Power': power[0]
        #Energy
        #SwitchStates :[0,1,1]
        } )
        msg = str(data)
        return msg
    
    #modes: faulty o blackout
    #faulty : range simulazione vengono presi da faulty_simualtion.json
    #non vanno tv e washing machine (modulo 1 e 2)
    #blackout: 5 elettrodmestici con misurazione di tensione anomale
    #maxpower : D11 (heater) supera maxpower
    #contatore: potenza supera quella massima supportata dal contatore
    #normal : funziona senza problemi
    def ApplianceEmulator(self,devID,mode):
        jsonfile=None
        if mode=='faulty':
            jsonfile=self.faulty
        elif mode == 'blackout': 
            jsonfile=self.blackout
        elif mode =='maxpower':
            jsonfile=self.maxPower
        elif mode=='contatore':
            jsonfile=self.contatore
        else: jsonfile=self.normal
        min_p=jsonfile[devID]['min']
        max_p=jsonfile[devID]['max']
        voltage=jsonfile[devID]['voltage']
        power=np.random.randint(min_p,max_p, 1)
        current= power/voltage
        digits = re.findall(r'\d+', devID)
        ID_num = ''.join(digits)
        ID= 'D' + str(ID_num)
        data = ( {
        'socketID': ID,
        'voltage': voltage,
        'current': current[0],
        'power': power[0]
        } )
        msg = str(data)
        return msg 

        


