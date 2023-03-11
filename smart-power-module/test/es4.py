#SUBSCRIBER
import json
import time
import json_management as m
from MyMQTT import MyMQTT


class Sub:
    def __init__(self, clientID, topic, broker, port):
        self.client = MyMQTT(clientID, broker, port, self)
        self.topic = topic     

    def start(self):
        self.client.start()
        self.client.mySubscribe(self.topic)

    def stop(self):
        self.client.stop()

    def notify(self, topic, msg):

        d = json.loads(msg)
        power = d["power"]
        voltage = d["voltage"]
        current = d["current"]
        timestamp = d["timestamp"]  
        msgs = [ {"bn": "http://example.org/sensor1/",
                  "e": [
                 { "n": "Power", "u": "W", "t": timestamp, "v": power }, 
                 { "n": "Voltage", "u": "V", "t": timestamp, "v": voltage  },   
                 { "n": "Current", "u": "A", "t": timestamp,"v": current    }]}]  
        #with open('out.json', 'r') as f:
            #file_json = json.load(f)           
        #file_json['e'].extend(msgs) # Append list instead of dictionary
        with open('out.json', 'w') as f:
            json.dump(msgs, f, indent=2)
        


if __name__ == "__main__":
    conf = json.load(open("settings.json"))
    broker = conf["broker"]
    port = conf["port"]
    test = Sub("MyLed", "IoT/miri/led", broker, port)
    test.start()

    while True:
        time.sleep(1)

    test.stop()


