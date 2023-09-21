#include "HardwareSerial.h"
#include "configs.h"
#include "comm.h"

WiFiClient wifiClient;  
PubSubClient mqttClient(mqttBroker.c_str(), mqttPort, mqttCallback, wifiClient);

Scheduler nodeScheduler;
painlessMesh socket_mesh;
Task MeshSender(TASK_SECOND * SAMPLE_PERIOD, TASK_FOREVER, &sendData2Mesh);

void setup_wifi() {
  //delay(100);
  WiFi.mode(WIFI_AP_STA);
  MAC = WiFi.macAddress();
  // We start by connecting to a WiFi network
 
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.print(wifiSSID);
  
  WiFi.begin(wifiSSID, wifiPWD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
 
  Serial.println("");
  Serial.println("WiFi connected");
  
  Serial.print("Current IP address: ");
  Serial.println(WiFi.localIP());

  Serial.print("Current WiFi channel: ");
  wifiChannel = WiFi.channel();
  Serial.println(wifiChannel);  

  //RSSI = WiFi.RSSI();
}

JSONVar get(String url, String params){
  HTTPClient http;

  JSONVar obj = JSON.parse(params);
  JSONVar keys = obj.keys();

  Serial.println(params);

  url+="?";
  for(int i=0; i<keys.length(); i++){
    String key = JSON.stringify(keys[i]);
    String value = JSON.stringify(obj[keys[i]]);

    key.replace("\"", "");
    value.replace("\"", "");

    url += key;
    url += "=";
    url += value;
    if(i != keys.length()-1){
      url += "&";
    }
  }

  //Serial.println(url);

  http.begin(url.c_str());

  http.addHeader("Content-Type", "text/plain");

  int httpResponseCode = http.GET();

  String payload = "{\"status\":\"Error\"}";

  if (httpResponseCode>0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    payload = http.getString();
    Serial.println(payload);
  }
  else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();

  return JSON.parse(payload);
}

void findSystem(){
  while(mdns_init()!= ESP_OK){
    delay(1000);
    Serial.println("Starting MDNS...");
  }
 
  Serial.println("MDNS started");

  IPAddress trueIP;
  while (trueIP.toString() == "0.0.0.0") {
    Serial.println("Resolving host...");
    delay(250);
    String host = system_mDNS;
    host.replace(".local", "");
    trueIP = MDNS.queryHost(host);
  }
  Serial.print("Host resolved: ");
  Serial.println(trueIP);
  connectorIP = trueIP.toString();
}

void setup_mqtt(){
  Serial.print("connecting to mqtt broker...");
  while (!mqttClient.connect(clientID.c_str())) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println(" connected to broker!");
}
void onConnectionEstablished(){
  Serial.println("Connected to broker");
}
void mqttCallback(char* topic, uint8_t* payload, unsigned int length){
  char* cleanPayload = (char*)malloc(length+1);
  payload[length] = '\0';
  memcpy(cleanPayload, payload, length+1);
  String msg = String(cleanPayload);
  free(cleanPayload);

  String targetStr = String(topic);

  onMQTTReceived(targetStr, msg);
}

void init_mesh(){
  socket_mesh.setDebugMsgTypes( ERROR | STARTUP | MESH_STATUS | CONNECTION );  // set before init() so that you can see startup messages

  if(masterNode){
    socket_mesh.init( MESH_PREFIX, MESH_PASSWORD, MESH_PORT, WIFI_AP_STA, wifiChannel);
  } else {
    socket_mesh.init( MESH_PREFIX, MESH_PASSWORD, &nodeScheduler, MESH_PORT, WIFI_AP_STA, wifiChannel);
  }

  Serial.println("Started mesh network.");

  if(masterNode){
    socket_mesh.onReceive(&onRecMeshMsgBridge);
  } else {
    socket_mesh.onReceive(&onRecMeshMsg);
  }
  socket_mesh.onNewConnection(&newConnectionCallback);

  if(masterNode){
    socket_mesh.stationManual(wifiSSID, wifiPWD);
    socket_mesh.setHostname(systemName);
    Serial.println("Set station settings.");
  } else {
    nodeScheduler.addTask(MeshSender);
    MeshSender.enable();
  }
  if(masterNode) {
    socket_mesh.setRoot(true);
    socket_mesh.setContainsRoot(true);
  }
  /*mesh.onChangedConnections(&changedConnectionCallback);
  mesh.onNodeTimeAdjusted(&nodeTimeAdjustedCallback);*/
}
void newConnectionCallback(uint32_t nodeId) {
  Serial.printf("New Connection, nodeId = %u\n", nodeId);
}
void sendMeshMsg(String payload){
  socket_mesh.sendBroadcast(payload);
  Serial.println("Sent " + payload + " to mesh.");
}
