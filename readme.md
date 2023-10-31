## Running the system ##

### First run ##
The first time the system is turned on some additional configuration steps must be taken:

1. Launch the [start_System.py](https://github.com/morgancasale/smart-power-module/blob/main/start_System.py) script which will automatically update some configuration parameters in the ESP32 Firmware (more info in the firmware [readme](https://github.com/morgancasale/smart-power-module/blob/main/ESP32Firmware/readme.md)), build all the system's docker containers and then compose up the system.

2. Open in your browser the [Home Assistant Interface](http:/127.0.0.1:8123) on the same computer where docker is running and follow the registration steps.

3. After reaching the Home Assistant dashboard the [after_HA.py](https://github.com/morgancasale/smart-power-module/blob/main/after_HA.py) script must be run to setup the MQTT and localIP integrations needed for Home Asistant to work with the system.

4. Follow closely the steps given by the [after_HA.py](https://github.com/morgancasale/smart-power-module/blob/main/after_HA.py) script.

5. Now in the dashboard the IP of the system will be shown, take note of it as it will be useful to open the Home Assistant interface from other devices. \
This can be achieved by opening the url `http://systemIP:8123`.

6. Some features will not be available until at least one esp32 is flashed with the [firmware](https://github.com/morgancasale/smart-power-module/tree/main/ESP32Firmware) and turned on.

7. `Enjoy`!

### Following runs ###
To run the system again one must only run the command `docker compose up` inside the smart-power-module root directory.

### Data Generation ###

Running the code in "modulesEmulator.py" it is possible to generate data and register devices.

To register devices for the first time these two lines of code should be used:\
            #self.deviceReg()\
            #json.dump(self.devices, open('modulesEmulator/devices.json', 'w'))
            
If the devices are already registered instead this line is needed:        
            #self.devices = json.load(open('modulesEmulator/devices.json')) 
            
To publish data instead, this function should be used:\
            #self.publishApp('normal') 
            
Different types of data can be created, simulating many possible scenarios.
The different modes are:
    "faulty": some appliances are broken
    "blackout": a blackout is taking place
    "maxpower2: a module exceeds its power consumption limit
    "contatore": the power consumption of the house exceeds the limit of the electric meter
    "normal": no anomalies
    "standbypower": parasitic consumptions are detected

### Notes ###

- The Home Assistant integration used to calculate the cost of the consumed energy seem to not work in the current version of Home Assistant.
