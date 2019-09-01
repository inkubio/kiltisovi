import sys
import time
import atexit

import nfc
import RPi.GPIO as gpio
import requests


clf = nfc.ContactlessFrontend('ttyUSB0')
gpio.setmode(gpio.BCM)
gpio.setup(20, gpio.OUT)

atexit.register(gpio.cleanup)
atexit.register(clf.close)

API_URL = "https://inkubaattori.aalto.fi/ovi"

# Following codes are magic and specific to HSL travel cards
SELECT_APPLICATION = "90 5a 0000 03 1420ef 00"
SELECT_APPLICATION_OLD = "90 5a 0000 03 1120ef 00"
READ_ID = "90 bd 00 00 07 08 00 00 00 00 00 00 00"


""" Send command to reader to execute on tag """
def reader_cmd(tag, hexstring):
    return tag.transceive(bytearray.fromhex(hexstring)).hex()


"""
Attemps to read and return a card ID. First attempt is the newest 
HSL travel card, then it falls back to old HSL card, and last just
returns the card/tag UID
"""
def read():
    tag = clf.connect(rdwr={'on-connect': lambda tag: False})
    res = reader_cmd(tag, SELECT_APPLICATION)
    if res != "9100":
        res = reader_cmd(tag, SELECT_APPLICATION_OLD)
        if res != "9100":
            print("Unknown card uid: ", end="")
            return tag.identifier.hex(), False
        else:
            print("Old HSL id: ", end="")
    else:
        print("New HSL id: ", end="")
    res = reader_cmd(tag, READ_ID)
    return res[2:20], True


""" Opens the electric lock for {timeout} seconds """
def open(timeout=4):
    gpio.output(20, True)
    time.sleep(timeout)
    gpio.output(20, False)


""" Pretty printing of HSL card IDs """
def pretty(value):
    print("{} {} {} {}".format(value[:6], value[6:10], value[10:14], value[14:]))


print("Reading...")
while True:
    try:
        tag_id, tag_is_hsl = read()
        if tag_is_hsl:
            pretty(tag_id)
        else:
            print(tag_id)

        ret = requests.post(API_URL + "/check", data={"id": tag_id})
        if ret.status_code == 200:
            open()
        else:
            print("Unauthorized.")

    except Exception as e:
        print(e)
