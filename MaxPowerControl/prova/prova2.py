#funzione da inserire nel file principale(?)
def myMQTTfunction(self, houseID, deviceID):
    deviceID=self.controlLastUpdateModule(houseID)
    MQTT=ServiceBase("serviceConfig_example.json")
    topic="{}/{}".format(houseID,deviceID)
    msg =[{"MaximumPowerControl:"{
           "Active": {
           "moduleState":0 
           }
           }}
        ]
    MQTT.start()
    MQTT.Subscribe(topic)
    MQTT.Publish(topic, msg)
    MQTT.stop()