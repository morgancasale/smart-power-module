#ifndef sensor_h
#define sensor_h
  #include <OneWire.h>
  #include <DallasTemperature.h>
  #define ONE_WIRE_BUS 4

  float read_temp();

#endif