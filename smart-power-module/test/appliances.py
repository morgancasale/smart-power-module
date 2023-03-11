import numpy as np
import numpy as np
import matplotlib.pyplot as plt


class Appliances():

    def voltage_emulator_wm(self):
        noise = np.random.randint(-1,1,self.time_int)
        self.voltage=np.zeros(self.time_int)
        v = np.random.default_rng().normal(220, 2, 70)
        for i in range(70):
            in_=60*i
            f=60*(i+1)
            self.voltage[in_:f]=v[i]
        voltage_n= self.voltage + noise
        #plt.plot(X,voltage_n)
        #plt.show()
        return voltage_n

    def current_emulator_wm(self):
        current = self.Y/self.voltage
        return current


    def washing_machine(self): #power
        
        self.time_int=4200
        #heating phase 1
        x_heating_values_1=s = np.linspace(0,1079,1080)# 1 dato al secondo per 18 minuti, 2000,2200
        y1=[2100]*1080
        #heating phase 2
        x_heating_values_2=s = np.linspace(1080,1320,240)# 1 dato al secondo per 4 minuti. 0,100,
        y2=[50]*240
        #heating phase 3
        x_heating_values_3=s = np.linspace(1321,1380,60)# 1 dato al secondo per 1 minuti2000,2200,
        y3=[2100]*60
        #phase 4
        x_washing_values=  np.linspace(1381,2700,1320)#22 minuti 0,100
        y_wv=[50]*1320
        #spin cycle
        x_spin_values=np.linspace(2700, 2770, 70)#1 minuto, tra 50 e 400, 
        #y_sv=50+(np.exp(np.linspace(0,6,60)))
        y_sv=np.linspace(0,440,70)
        #washing values per 9 min
        x_washing_values_2=np.linspace(2770,3300,530)#0,150
        y_wv_2=[75]*530
        #spin cycle per 1 min
        x_spin_values_2=np.linspace(3300, 3370, 70)#1 minuto, tra 50 e 400, 
        y_sv_2=np.linspace(0,440,70)
        #wahing 2 per 9 minuti
        x_washing_values_3=np.linspace(3370,3900,530)#0,150
        y_wv_3=[75]*530
        #final spin 
        x_final_spin_values= np.linspace(3900,4200,300)
        y_fsv=np.linspace(50,500,80)
        y_fsv2=[450]*220

        #X=np.concatenate((x_heating_values_1,x_heating_values_2,x_heating_values_3,\
        #            x_washing_values,x_spin_values,x_washing_values_2,\
        #            x_spin_values_2,x_washing_values_3,x_final_spin_values))
        self.Y=np.concatenate((y1,y2,y3,y_wv,y_sv,y_wv_2,y_sv_2,y_wv_3,y_fsv,y_fsv2))

        noise1=np.random.exponential(scale=8,size=2100)
        noise2=-1*(np.random.exponential(scale=6,size=2100))
        noise=np.concatenate((noise1,noise2))
        np.random.shuffle(noise)
        self.Y=self.Y+noise
        time_int=len
        #plt.plot(X,Y)
        #plt.show()
        return self.Y
    
    def standByPowerEmulator(self): 
    #example using a microwave. In addition to using energy while cooking or heating,
    #a  microwave will also use (1) 2 to  7 watts of power while in standby mode. 
        power=np.random.randint(1,8,60)  #noise?
        voltage=np.ones(60)*220
        current= np.divide(power,voltage) #ceck that this is element wise
        return power,voltage, current
        #to_gen = 60
        
    
    def BlackoutBrownoutEmulator(self):
    #example on values measured on tv, decrease rate for current and voltage is assumed to be the same
        voltage=np.arange(220, 160,-3) #voltage -25% 
        current=np.arange(0.51, 0.37, -0.007)
        power=np.multiply(voltage, current)
        return power, voltage, current 
        #to_gen=20                        



