#!/usr/bin/env python3

import RPi.GPIO as GPIO
from time import sleep

GPIO_LT = 37
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(True)
GPIO.setup(GPIO_LT, GPIO.IN)

#while (True):
#    if (GPIO.input(GPIO_LT == 1)):
#            print("Black detected!")
#    else:
#        print("Black out of reach!")
#
#    print("")

while True:
    print(GPIO.input(GPIO_LT))
    sleep(0.5)

GPIO.cleanup()
