## Setup ##

### Adding Required ESP-32 Libraries ###

To flash firmware to ESP32 boards using the Arduino IDE some steps must be first taken.

Most boards use the Silabs CP210x USB to UART chip, for which you have to install the driver:

1. Go to [Silicon Labs' official driver download page](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
2. Go to the downloads section and download the "CP210x Windows Drivers" (third in the list).
3. Extract the .zip and run `CP210xVCPInstaller_x64.exe`.
4. Your ESP32 should now show up in your devices manager under ports as `Silicon Labs CP210x USB to UART Bridge (COM<number>)`. This is the port you should select in your IDE. If it doesn't show up, make sure you are using a data capable USB cable.

Adding the ESP32 package to your Arduino IDE:

1. Go to File > Preferences in your Arduino IDE
2. In the "Additional Board Manager URLs" field, enter this link: https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json and click the OK button
3. Go to Tools > Board > Boards Manager
4. Search "esp32" and install the "ESP32 by Espressif Systems" package, `version 2.0.11 must be installed` as later versions seem to break the ESPMesh feature.
5. Select your ESP32 board from Tools > Board  (Use ESP32 Dev Module if you are unsure)

### Required Arduino libraries ###

Before flashing the firmware onto any ESP32 board some Arduino libraries must be installed:

- `Arduino_Json` by Arduino
- `ArduinoJson` by Benoit Blanchon (both json libraries needs to be installed)
- `AsyncTCP` by dvarrel
- `EspMQTTClient` by Patrick Lapointe
- `Painless Mesh` by Coopdis, Scotty Franzyshen, Edwin van Leeuwen, Germán Martín, Maximilian Schwarz, Doanh Doanh
- `PubSubClient` by Nick O'Leary
- `TaskScheduler` by Anatoli Arkhipenko

### Configurable parameters ###

In the `configs.h` and `configs.cpp` files are written all the parameters used by the firmware.\
If the [system starter script](https://github.com/morgancasale/smart-power-module/blob/main/start_System.py) was used correctly on the first system run, all the parameters should already be set to the right values.

If not three parameters must be changed manually in `configs.h`:

- `wifiSSID` - The SSID of the router to which is connected the running system.
- `wifiPWD` - The password of the router to which is connected the running system.
- `system_mDNS` - This is the mDNS to which the boards will try to send REST requests, it must be the name of the computer running the system followed by ".local". Ex. If computer is named "steven" the mDNS will be "steven.local"

The computer name can be found on linux by running the command `hostname` in the terminal.


