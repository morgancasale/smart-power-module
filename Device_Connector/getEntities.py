import requests
import json

system = "SSCK"

template = """{% set devices = states | map(attribute='entity_id') | map('device_id') | unique | reject('eq',None) | list %}
    
    {%- set ns = namespace(devices = []) %}
    {%- for device in devices %}
      {%- set ids = (device_attr(device, "identifiers") | list)[0] | list -%}
      {%- if "mqtt" in ids %}
        {%- set entities = device_entities(device) | list %}
        {%- if entities %}
          {%- set ns.devices = ns.devices + 
          [ {
            device: {"name": device_attr(device, "name"), "entities":entities, "identifiers" : ids}
            } ] %}
        {%- endif %}
      {%- endif %}
    {%- endfor %}
    {{ ns.devices }}"""

url = "%s:%s/api/template" % (
    "http://192.168.2.163", 
    str(8123)
)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzNjlmNWFiMzQ3Nzk0NTExYjAwZDE0YzA5ZTVkYmUwMCIsImlhdCI6MTY4MTczNzc2NiwiZXhwIjoxOTk3MDk3NzY2fQ.gn76jF7NYDzAxhW4tiQZ9kfD8K3TaTqGE__z_7xChOU"
headers = {
    "Authorization": "Bearer " + token,
    'content-type': "application/json",
}

test = "It is {{now()}}"
response = requests.post(url, headers=headers, data=json.dumps({"template": template}))
text = response.text.replace("\'", "\"")
response = json.loads(text)

