#include "xt_instr_macros.h"
#ifndef configs_h
#define configs_h
  #include "Arduino.h"

  #define wifiSSID "Belkincul-"
  #define wifiPWD "ravintolakuparipannu2"
  #define hostName "SmartSocket"
  #define connectorIP "192.168.2.145"
  #define connectorPort 8067

  #define autoBroker true
  #define autoTopics true
  
  #define MESH_PREFIX "Socket_Mesh"
  #define MESH_PASSWORD "oppioppi"
  #define MESH_PORT 5555

  #define SAMPLE_PERIOD 10 // in seconds

  extern String MAC;
  extern int wifiChannel;
  extern int16_t RSSI;

  extern String clientID;
  extern String mqttBroker;
  extern int mqttPort;
  extern String mqttUSR;
  extern String mqttPWD;
  extern String subTopic;
  extern String pubTopic;

  extern String socketID;
  extern bool masterNode;
  extern uint8_t masterMAC[6];
  extern uint8_t slaveMAC[6];

#endif