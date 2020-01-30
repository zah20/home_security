#!/usr/bin/env python3

from time import sleep
from picamera import PiCamera

def main():
    global camera

    camera = PiCamera()

    captureVideo()
    camera.close()



def captureImage(timeFrame=1):
    global camera
    camera.start_preview()
    sleep(timeFrame)
    camera.capture('test.jpg')
    camera.stop_preview()

def captureVideo(timeFrame=10, fileName='test.h264'):
    global camera
    camera.start_preview()
    camera.start_recording(fileName)
    sleep(timeFrame)
    camera.stop_recording()
    camera.stop_preview()










if __name__ == '__main__':
    main()
