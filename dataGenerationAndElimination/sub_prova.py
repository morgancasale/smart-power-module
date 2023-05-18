import paho.mqtt.client as mqtt
import json


conf_t = json.load(open('C:/Users/hp/Desktop/IOT/lab4_es4/deviceConn_sens/topic.json'))
topics = conf_t["topics"]

# Define the callback function to handle incoming messages
def on_message(client, userdata, message):
    print(f"Received message on topic '{message.topic}': {message.payload.decode()}")

# Create a MQTT client instance
client = mqtt.Client()

# Set the callback function for incoming messages
client.on_message = on_message

# Connect to the MQTT broker
#client.connect("mqtt.eclipseprojects.io", 1883)
client.connect("broker.emqx.io", 1883)

# Subscribe to topics
for topic in topics:
    client.subscribe(topic)
    print(f"Subscribed to '{topic}' topic")

# Start the MQTT client loop to receive incoming messages
client.loop_start()

# Keep the program running to receive messages
while True:
    pass

# Stop the MQTT client loop
client.loop_stop()
