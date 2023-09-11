// the setup function runs once when you press reset or power the board
#include "configs.h"
#include "comm.h"
#include "sensor.h"
#define LED_BUILTIN 2

TaskHandle_t parLoop;
int SwitchStates[3]={0,0,0};

void onMQTTReceived(String topic, String msg){
  Serial.print("Received MQTT message: ");
  Serial.println(msg);

  JSONVar payload = JSON.parse(msg);
  
  if(fixJSONString(payload["deviceID"]) != deviceID){
    socket_mesh.sendBroadcast(msg);
  } else if (fixJSONString(payload["deviceID"]) == deviceID){
    digitalWrite (LED_BUILTIN, payload["state"]);
    SwitchStates[(int)payload["plugID"]] = (int) payload["state"];
  }
}

unsigned long prevTime = 0;
void onRecMeshMsgBridge(uint32_t from, String &data) {
  Serial.println("Received data from node " + String(from));
  if(mqttClient.publish(pubTopic.c_str(), data.c_str())){
    Serial.println("Published at " + pubTopic + " : " + data);
  } else {
    Serial.println("Error while publishing to broker!");
  }

  unsigned long now = millis();
  if(now-prevTime>10000){
    sendData2MQTT();
    prevTime = now;
  }
}

void onRecMeshMsg(uint32_t from, String &data) {
  Serial.print("Received data from node " + String(from));
  Serial.println(" : "+ data);
  JSONVar payload = JSON.parse(data);
  String temp = JSON.stringify(payload["deviceID"]);
  if(temp == deviceID || temp == "*" ){
    digitalWrite (LED_BUILTIN, payload["state"]);
    SwitchStates[(int) payload["plugID"]] = (int) payload["state"];
  }
}

void readSwitchStates(JSONVar &payload){
  payload["SwitchStates"][0] = (int) SwitchStates[0];
  payload["SwitchStates"][1] = (int) SwitchStates[1];
  payload["SwitchStates"][2] = (int) SwitchStates[2];
}

void sendData2Mesh(){
  float temp = random(250,340)/10;

  JSONVar payload;
  payload["deviceID"] = deviceID;
  payload["Voltage"] = (float) temp*10;
  payload["Current"] = (float) temp*0.4;
  payload["Power"] = (float)temp*10 * (float)temp*0.4;
  payload["Energy"] = (float) (temp+10)/3;
  readSwitchStates(payload);

  sendMeshMsg(JSON.stringify(payload));
}

void sendData2MQTT(){
  float temp = random(23, 24)+random(0,100)/100;

  JSONVar payload;
  payload["deviceID"] = deviceID;
  payload["Voltage"] = (float) temp*10;
  payload["Current"] = (float) temp*0.4;
  payload["Power"] = (float)temp*10 * (float)temp*0.4;
  payload["Energy"] = (float) (temp+10)/3;
  readSwitchStates(payload);

  String data = JSON.stringify(payload);
  if(mqttClient.publish(pubTopic.c_str(), data.c_str())){
    Serial.println("Published at " + pubTopic + " : " + data);
  } else {
    Serial.println("Error while publishing to broker!");
  }
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
  //params["RSSI"] = RSSI;
  params["autoBroker"] = autoBroker;
  params["autoTopics"] = autoTopics;

  Serial.print("Sending GET request with params: ");
  JSONVar response = get(url, JSON.stringify(params));

  deviceID = fixJSONString(response["deviceID"]);
  masterNode = (bool)response["masterNode"];
  Serial.println(masterNode);

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
  Serial.print(deviceID);
  Serial.println(".");

  clientID = deviceID;
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

          /*unsigned long now = millis();
          if(now-prevTime>10000){
            sendData2MQTT();
            prevTime = now;
          }*/
        }
      }
    }
  }
}

// the loop function runs over and over again forever
void loop() {
  socket_mesh.update();
}

void setup() {
  randomSeed(analogRead(0));
  // initialize digital pin LED_BUILTIN as an output.
  pinMode (LED_BUILTIN, OUTPUT);

  Serial.begin (115200); 

  Serial.print("Setup running on core ");
  Serial.println(xPortGetCoreID());

  setup_wifi();

  findSystem();

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