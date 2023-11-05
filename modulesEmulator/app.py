import json
import re
import os
import random

IN_DOCKER = os.environ.get("IN_DOCKER", False)

class Appliances():
    def __init__(self) :
        if(not IN_DOCKER):
            folder_loc = "modulesEmulator/"
        else:
            folder_loc = ""
       
        self.faulty=json.load(open(folder_loc + 'faulty_simulation.json'))
        self.blackout=json.load(open(folder_loc + 'blackout_simulation.json'))
        self.maxPower=json.load(open(folder_loc + 'maxPower.json'))
        self.contatore=json.load(open(folder_loc + 'contatore.json'))
        self.normal=json.load(open(folder_loc + 'normalFunctioning.json'))

    def standByPowerEmulator(self,devID): #possono avere tutti stesso perchè range molto simile
        devID= 'D' + str(devID)
        digits = re.findall(r'\d+', devID)
        ID_num = ''.join(digits)
        ID= 'D' + str(ID_num)
        power = round(random.uniform(1,5), 2)
        v_min=229
        v_max=232
        voltage = round(random.uniform(v_min,v_max),2)
        current = round(power/voltage, 2)
        energy_ws = round(power * 2, 2)
        energy_kwh = round(energy_ws / (3600 * 1000), 2)
        data = ( {
            'deviceID': devID,
            'Voltage': voltage,
            'Current': current,
            'Power': power,
            'Energy': energy_kwh,
            'switch_state' : [1,0,0]
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
    def ApplianceEmulator(self,dev, mode):
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
        min_p=jsonfile[dev["MAC"]]['min']
        max_p =jsonfile[dev["MAC"]]['max']
        v_min=jsonfile[dev["MAC"]]["voltage_min"]
        v_max=jsonfile[dev["MAC"]]["voltage_max"]
        voltage = round(random.uniform(v_min,v_max), 2)
        power = round(random.uniform(min_p,max_p), 2)
        current = round(power/voltage, 2)
        energy_ws =  round(power * 2, 2)
        energy_kwh = round(energy_ws / 3600 * 1000, 2)
        data = {
            'deviceID': dev["deviceID"],
            'Voltage': voltage,
            'Current': current,
            'Power': power,
            'Energy': energy_kwh,
            'SwitchStates' : [1,0,0]
        }
        msg = json.dumps(data)
        return msg 

