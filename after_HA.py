import webbrowser
import requests
import subprocess

"""
Run this script on the host computer after Home Assistant is up and running.
"""

def open_web_page(url):
    ps = subprocess.Popen(["dpkg", "--get-selections"], stdout=subprocess.PIPE)
    cmd_result = subprocess.check_output(["grep", "browser"], stdin=ps.stdout)
    ps.wait()

    browser = cmd_result.decode().split("\t")[0]

    webbrowser.get(browser).open(url)

try:
    # Open the web browser to the Home Assistant page where to configure the MQTT integration
    url = "http://127.0.0.1:8123/_my_redirect/config_flow_start?domain=mqtt"
    open_web_page(url)

    # Get the MQTT broker info from the catalog
    url = "http://127.0.0.1:8099/getInfo"
    params = {
        "table": "EndPoints",
        "keyName": "endPointName",
        "keyValue": "MQTTBroker"
    }

    response = requests.get(url, params=params)
    if(response.status_code != 200):
        raise Exception("Error while retriving broker info from catalog")

    brokerInfo = response.json()[0]

    print("For the next steps, please use the following info:")
    print("Broker address: " + brokerInfo["IPAddress"])
    print("Broker port: " + str(brokerInfo["port"]))
    print("Broker username: " + brokerInfo["MQTTUser"])
    print("Broker password: " + brokerInfo["MQTTPassword"])
    print("")

    input("Press Enter to continue...")

    # Open the web browser to the Home Assistant page where to configure the localIP integration
    url = "http://127.0.0.1:8123/_my_redirect/config_flow_start?domain=local_ip"
    open_web_page(url)
except Exception as e:
    print(str(e))
