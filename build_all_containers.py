import os

images = [
    "resourceCatalog",
    "deviceConnector",
    "onlineTracker",
    "blackoutFaultyDetection",
    "maxPowerControl",
    "moduleConsumptionControl",
    "standByPowerDetection",
    "timeShift"
]

for image in images:
    docker_file = image + "/dockerfile"
    image_name = image.lower()
    print("Building image %s" % image_name)
    os.system("docker build -t %s -f %s ." % (image_name, docker_file))
    print("Image %s built" % image_name)
    print("")