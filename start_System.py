import json
import os
import subprocess
import re

def build_images(images):
    print("Starting docker images building process...\n")
    print()

    for image in images:
        docker_file = image + "/dockerfile"
        image_name = image.lower()
        print("Building image %s" % image_name)
        os.system("docker build -t %s -f %s ." % (image_name, docker_file))
        print("Image %s built" % image_name)
        print("")

def get_save_hostname():
    cmd_result = subprocess.run(["hostname"], stdout=subprocess.PIPE)
    global hostname
    hostname = cmd_result.stdout.decode().replace("\n", "")
    generalStgs["hostname"] = hostname
    with open("general.json", 'w') as file:
        json.dump(generalStgs, file, indent=4)

def get_WIFI():
    print("WiFi SSID and password of this device will be now read")
    input("Press Enter to continue...")

    cmd_result = subprocess.run(["nmcli", "device", "wifi", "show-password"], stdout=subprocess.PIPE)

    info = cmd_result.stdout.decode().split("\n")
    
    global SSID 
    SSID = info[0].split(" ")[1]
    global PWD 
    PWD = info[2].split(" ")[1]

def update_ESP_config():
    print("Updating ESP32 firmware configs...")
    print()

    config = open("ESP32Firmware/configs.h", "r+")
    content = config.read()

    content = re.sub('wifiSSID "([^"]+)"', "wifiSSID \""+SSID+"\"", content)
    content = re.sub('wifiPWD "([^"]+)"', "wifiPWD \""+PWD+"\"", content)
    content = re.sub('system_mDNS "([^"]+)"', "system_mDNS \""+hostname+".local\"", content)

    config.truncate(0)
    config.close()

    config = open("ESP32Firmware/configs.h", "w")
    config.write(content)
    config.close()

hostname = ""
SSID = ""
PWD = ""
generalStgs = json.load(open("general.json", 'r'))

if(generalStgs["hostname"] == None):
    get_save_hostname()
    get_WIFI()
    update_ESP_config()
    build_images(generalStgs["images"])


os.system("docker compose up")


