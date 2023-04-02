import random
import base64

def randomB64String(length):
    num = int("".join(["9"] * length))
    return str(base64.b64encode(str(random.randint(0, num)).encode("ascii")))[2:length+2]