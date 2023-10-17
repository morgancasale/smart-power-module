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
        self.threads = [] 
        self.running = 0
        self.devices = json.load(open("C:/Users/mirip/Desktop/smart-power-module-main/modulesEmulator/devices.json"))
        self.pubTopic = "smartSocket/data"
        try:
            self.configFile_loc = "modulesEmulator.json"
            if(not IN_DOCKER):
                self.configFile_loc = "modulesEmulator/" + self.configFile_loc
            self.client = ServiceBase(self.configFile_loc)
            self.client.start()
            self.appClient = Appliances()
            print("Emulator started")
            #self.deviceReg()
            json.dump(self.devices, open('modulesEmulator/devices.json', 'w'))

            self.devices = json.load(open('modulesEmulator/devices.json'))
            
            self.publishApp('normal')

            #self.publishDB("modulesEmulator/hist_data.db")
        except HTTPError as e:
            message = "An error occurred while running the service: \u0085\u0009" + e._message
            raise Exception(message)
        except Exception as e:
            message = "An error occurred while running the service: \u0085\u0009" + str(e)
            raise Exception(message)

    #modes: standbypower, faulty, blackout,maxpower, contatore, normal
    def messageGenerator(self, mode, dev):
        if mode == 'standbypower':
            msg=self.appClient.standByPowerEmulator(dev)
        else:
            msg=self.appClient.ApplianceEmulator(dev, mode)
        return msg

    def deviceReg(self):
        self.devices = []
        data_reg = json.load(open('modulesEmulator/registration.json'))
        catalog_address = self.client.generalConfigs["REGISTRATION"]["catalogAddress"]
        catalog_port = self.client.generalConfigs["REGISTRATION"]["catalogPort"]
        
        url="%s:%s/getInfo"%(catalog_address, str(catalog_port))
        params={
        "table" : "EndPoints",
        "keyName" : "endPointName",
        "keyValue" : "deviceConnector"
        }  
        response = requests.get(url, params=params)
        response = response.json()[0]
        endpoint = response
        port = endpoint['port']

        url_dc=  str(catalog_address)+ ":" + str(port) + "/getRole"
        for entry in data_reg["entries"]:
            print(entry)
            mac = entry["MAC"]
            auto_broker = entry["autoBroker"]
            auto_topics = entry["autoTopics"]
            params_dc={
                "MAC": mac,
                "autoBroker": auto_broker,
                "autoTopics": auto_topics,
                "autoMasterNode": False
            }  
            response = requests.get(url_dc, params=params_dc)
            dev = {
                "MAC": mac,
                "deviceID": response.json()["deviceID"]
            }
            self.devices.append(dev)
            time.sleep(10)

    def publishDB(self, dataDB_path):
        try:
            conn = sq.connect(dataDB_path)
            prev_row = 0
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM states"
            num_rows = cursor.execute(query).fetchone()[0]

            query = """
                SELECT * FROM states 
                LIMIT 1 OFFSET %s;
            """ % str(prev_row)
            start_time = pd.read_sql_query(query, conn)
            start_time = start_time.to_dict(orient="records")
            start_time = start_time[0]["timestamp"]
            now = time.time()
            diff = now - start_time

            while prev_row < num_rows:
                current_time = str(time.time()-diff)
                query ="""
                    SELECT *
                    FROM states
                    WHERE timestamp < %s
                    LIMIT -1 OFFSET %s;
                """ % (current_time, str(prev_row))
                sel_rows = pd.read_sql_query(query, conn).to_dict(orient="records")

                prev_row += len(sel_rows)

                print("Current reached line: %s" % str(prev_row))

                for sel_row in sel_rows:
                    self.sendData(sel_row)
                time.sleep(5)
        except Exception as e:
            print(e)

    def sendData(self, sel_row):
        index = next((index for (index, d) in enumerate(self.devices) if d["MAC"] == sel_row["id"]), None)
        deviceID = self.devices[index]["deviceID"]
        switch_states = [-1, -1, -1]
        if sel_row["switch1"] != None: switch_states[0] = int(sel_row["switch1"] == "on")
        if sel_row["switch2"] != None: switch_states[1] = int(sel_row["switch2"] == "on")
        if sel_row["switch3"] != None: switch_states[2] = int(sel_row["switch3"] == "on")

        data = {
            "deviceID": deviceID,
            "Voltage": sel_row["voltage"],
            "Current": sel_row["current"],
            "Power": sel_row["power"],
            "Energy": sel_row["energy"],
            "SwitchStates" : switch_states
        }
        msg = json.dumps(data)
        self.client.MQTT.Publish(self.pubTopic,msg, talk= True)   


    #modes: faulty o blackout
    #faulty : range simulazione vengono presi da faulty_simualtion.json
    #non vanno tv e washing machine (modulo 1 e 2)
    #blackout: 5 elettrodmestici con misurazione di tensione anomale
    #maxpower : D11 (heater) supera maxpower
    #contatore: potenza supera quella massima supportata dal contatore
    #normal : funziona senza problemi
    #standbypower
    def publishApp(self, mode):
        print(self.devices)
        for dev in self.devices:
            thread = threading.Thread(target=self.deviceSim, args=(mode, dev))
            thread.start()
            
    def deviceSim(self, mode, dev):
        while True:
            msg = self.messageGenerator(mode, dev)
            self.client.MQTT.Publish(self.pubTopic,msg, talk=True)
            time.sleep(8)  

if __name__ == "__main__":
    Emulator()