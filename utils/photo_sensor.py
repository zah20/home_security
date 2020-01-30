#!/usr/bin/env python3 

import RPi.GPIO as GPIO
import time


pin = 26
GPIO.setmode(GPIO.BCM)

def rc_time(pin):
    count = 0

    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.setup(pin, GPIO.IN)

    while (GPIO.input(pin) == GPIO.LOW):
        count += 1

    return count

print(rc_time(pin))




