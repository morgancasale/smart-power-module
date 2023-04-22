// the setup function runs once when you press reset or power the board
#include "configs.h"
#include "comm.h"
#include "sensor.h"

TaskHandle_t parLoop;

void onMQTTReceived(String topic, String msg){
  Serial.print("Received MQTT message: ");
  Serial.println(msg);
  socket_mesh.sendBroadcast(msg);
}

void onRecMeshMsgBridge(uint32_t from, String &data) {
  Serial.println("Received data from node " + String(from));
  if(mqttClient.publish(pubTopic.c_str(), data.c_str())){
    Serial.println("Published at " + pubTopic + " : " + data);
  } else {
    Serial.println("Error while publishing to broker!");
  }
}

void onRecMeshMsg(uint32_t from, String &data) {
  Serial.print("Received data from node " + String(from));
  Serial.println(" : "+ data);
  JSONVar payload = JSON.parse(data);
  if(payload["socketID"] == socketID){
    digitalWrite (LED_BUILTIN, payload["state"]);
  }
}

void sendData(){
  float temp = read_temp();

  JSONVar payload;
  payload["socketID"] = socketID;
  payload["temperature"] = (float) temp;

  sendMeshMsg(JSON.stringify(payload));
}

String fixJSONString(JSONVar var){
  String result = JSON.stringify(var);
  result.replace("\"", "");
  result.replace("\"", "");
  return result;
}

void getRole(){
  String url = "http://" + String(connectorIP);
  url += ":" + String(connectorPort) + "/getRole";
  JSONVar params;
  params["MAC"] = MAC;
  params["RSSI"] = RSSI;
  params["autoBroker"] = autoBroker;
  params["autoTopics"] = autoTopics;

  Serial.print("Sending GET request with params: ");
  JSONVar response = get(url, JSON.stringify(params));

  socketID = fixJSONString(response["socketID"]);
  masterNode = (bool)(int)response["masterNode"];

  if(autoBroker){
    mqttBroker = fixJSONString(response["brokerIP"]);
    mqttPort = response["brokerPort"];
    mqttUSR = fixJSONString(response["brokerUser"]);
    mqttPWD = fixJSONString(response["brokerPassword"]);
  }

  if(autoTopics){
    subTopic = fixJSONString(response["subTopic"][0]);
    pubTopic = fixJSONString(response["pubTopic"][0]);
  }

  Serial.print("My subtopic is " + subTopic);
  Serial.print(" and my pubtopic "+ pubTopic);
  Serial.println(".");

  if(masterNode){
    Serial.print("I'm ");
  } else {
    Serial.print("I'm not ");
  }

  Serial.print("the masterNode and my ID is ");
  Serial.print(socketID);
  Serial.println(".");

  clientID = socketID;
}

IPAddress myIP = (0,0,0,0);
IPAddress getlocalIP() {
  return IPAddress(socket_mesh.getStationIP());
}

void loop2(void* pvParameters){
  for(;;){
    if(masterNode) mqttClient.loop();

    if(myIP != getlocalIP()){
      myIP = getlocalIP();
      Serial.println("My IP is " + myIP.toString());

      if(masterNode){
        if (mqttClient.connect(clientID.c_str(), mqttUSR.c_str(), mqttPWD.c_str())) {
          /*mqttClient.publish("painlessMesh/from/gateway","Ready!");
          mqttClient.subscribe("painlessMesh/to/#");*/
          mqttClient.subscribe(subTopic.c_str());
        } 
      }
    }
  }
}

// the loop function runs over and over again forever
void loop() {
  socket_mesh.update();
  /*if(masterNode) mqttClient.loop();

  if(myIP != getlocalIP()){
    myIP = getlocalIP();
    Serial.println("My IP is " + myIP.toString());

    if(masterNode){
      if (mqttClient.connect(clientID.c_str())) {
        mqttClient.subscribe(subTopic.c_str());
      } 
    }
  }*/
}

void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode (LED_BUILTIN, OUTPUT);

  Serial.begin (115200); 

  Serial.print("Setup running on core ");
  Serial.println(xPortGetCoreID());

  setup_wifi();

  getRole();

  WiFi.disconnect();
  //free((void*)wifiClient);*/

  init_mesh();

  xTaskCreatePinnedToCore (
    loop2,     // Function to implement the task
    "loop2",   // Name of the task
    4000,      // Stack size in bytes
    NULL,      // Task input parameter
    0,         // Priority of the task
    &parLoop,      // Task handle.
    0          // Core where the task should run
  );
}