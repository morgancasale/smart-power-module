#include "sensor.h"
OneWire oneWire(ONE_WIRE_BUS);

float read_temp(){
  DallasTemperature temp_sensor(&oneWire);

  float temp = 0;
  do{
    temp_sensor.requestTemperatures();
    temp = temp_sensor.getTempCByIndex(0);
  } while(temp < 0);
  
  return temp;
}
