#include "configs.h"

String MAC = "00:00:00:00:00:00";
int wifiChannel = 11;
int16_t RSSI = 0;

String clientID = "pixxapaxxa";
String mqttBroker = "broker.hivemq.com";
int mqttPort = 1883;
String mqttUSR = "public";
String mqttPWD = "public";
String subTopic = "smartSocket/control";
String pubTopic = "smartSocket/data";

String deviceID = "null";
bool masterNode = true;
uint8_t masterMAC[6] = {0xC8, 0xC9, 0xA3, 0xC9, 0x52, 0x80};
uint8_t slaveMAC[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
