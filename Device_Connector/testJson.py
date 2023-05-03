import json

if __name__=="__main__":
    with open('config.json', 'r+') as f:
        configs = json.load(f)
    configs = configs["MQTT"]
     

    topic = "broker/+/test"
    wildcard = ["#", "+"] #TODO controllare che non ci siano altri caratteri speciali
    if(any(w in topic for w in wildcard)):
        print("wildcard")