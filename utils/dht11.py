#!/usr/bin/env python3 

import Adafruit_DHT as DHT
import RPi.GPIO as GPIO
import time


pin = 26
GPIO.setmode(GPIO.BOARD)
sensor = DHT.DHT11


while True:
    humidity, temp = DHT.read_retry(sensor, pin)
    time.sleep(0.5)
    print("Temperature: %d\tHumidity: %d" % (temp, humidity))


