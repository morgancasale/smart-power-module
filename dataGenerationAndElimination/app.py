import numpy as np
import matplotlib.pyplot as plt
import json
import re

class Appliances():
    def __init__(self) :
        self.faulty=json.load(open('dataGenerationAndElimination/faulty_simulation.json'))
        self.blackout=json.load(open('dataGenerationAndElimination/blackout_simulation.json'))
        self.maxPower=json.load(open('dataGenerationAndElimination/maxPower.json'))
        self.contatore=json.load(open('dataGenerationAndElimination/contatore.json'))
        self.normal=json.load(open('dataGenerationAndElimination/normalFunctioning.json'))

    def standByPowerEmulator(self,devID): #possono avere tutti stesso perchè range molto simile
        devID= 'D' + str(devID)
        digits = re.findall(r'\d+', devID)
        ID_num = ''.join(digits)
        ID= 'D' + str(ID_num)
        power=np.random.randint(1,5, 1)
        voltage= 230
        current= power/voltage
        energy_ws = float(power[0]) * 2
        energy_kwh = energy_ws / (3600 * 1000)
        data = ( {
        'DeviceID': devID,
        'Voltage': voltage,
        'Current': current[0],
        'Power': power[0],
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
    def ApplianceEmulator(self,devID,mode):
        devID= 'D' + str(devID)
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
        energy_ws = float(power[0]) * 2
        energy_kwh = energy_ws / (3600 * 1000)
        data = ( {
        'DeviceID': devID,
        'Voltage': voltage,
        'Current': current[0],
        'Power': power[0],
        'Energy': energy_kwh,
        'switch_state' : [1,0,0]
        } )
        msg = str(data)
        return msg 

'''msg=  {
            "deviceID": ID,# string
            "Voltage": sensor_data[0] , #float
            "Current": sensor_data[1], #float
            "Power": sensor_data[2],#float
            "Energy":  sensor_data[3],#float
            "SwitchStates":socket #[ "int", "int", "int"]
        }'''
