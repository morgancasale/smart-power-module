import random
import base64

from threading import Thread, Event
import ctypes

from .Error_Handler import *

def randomB64String(length):
    result = "D'"
    while not result.isalnum():
        num = int("".join(["9"] * length))
        result = str(base64.b64encode(str(random.randint(0, num)).encode("ascii")))[2:length+2]

    return result