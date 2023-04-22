#ifndef comm_h
#define comm_h
  #include "Arduino.h"
  #include <WiFiClient.h>
  #include <HTTPClient.h>
  #include <PubSubClient.h>
  #include "painlessMesh.h"
  #include <Arduino_JSON.h>
  
  extern WiFiClient wifiClient;
  extern PubSubClient mqttClient;
  extern Scheduler nodeScheduler;
  extern painlessMesh socket_mesh;

  void setup_wifi();
  JSONVar get(String url, String params);

  void onConnectionEstablished();
  void setup_mqtt();
  void mqttCallback(char* topic, uint8_t* payload, unsigned int length);
  extern void onMQTTReceived(String topic, String msg);

  extern void init_mesh();  
  extern void newConnectionCallback(uint32_t nodeId);
  extern void sendMeshMsg(String payload);
  extern void onRecMeshMsgBridge(uint32_t from, String &data);
  extern void onRecMeshMsg(uint32_t from, String &data);
  extern void sendData();

  extern Task sender;

#endif