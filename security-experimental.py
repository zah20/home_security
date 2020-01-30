#!/usr/bin/env python3

###################################################
##                                               ##
## Author:  zah20                                ##
## Version: 0.2                                  ##
## Date:    10/6/2018                            ##
##                                               ##
###################################################

import smtplib, poplib
import RPi.GPIO as GPIO
import Adafruit_DHT as DHT
import multiprocessing as multiproc
from sys import exit
from time import sleep, time
from picamera import PiCamera
from os.path import basename
from os import system, popen, getcwd
from bluetooth import discover_devices as btscan
from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from email.mime.application import MIMEApplication



###############################################
#                  Main Function              #
###############################################

def main():

    ###############################################
    #               Global Variables              #
    ###############################################
    global minDistance, GPIO_TRIGGER, GPIO_ECHO, \
            GPIO_LED_BLUE, GPIO_LED_RED, GPIO_DHT, \
            camera

    global commandList, commandQueue, audioList, credentials, \
            userDataFile, whiteListedEmail, whiteListedBTDevice, \
            cmdActive, emailLock, audioLock, sleepEmailCheck, \
            remoteModule, localModule, localActive, localPID, \
            sensorDHT

    commandList = ['snap', 'text', 'quote', 'status']
    
    commandQueue = []

    audioList = ['audio/warning.wav', \
            'audio/greeting.wav', 'audio/goodbye.wav']

    credentials = ()
    userDataFile = 'config/userdata.dat'
    whiteListedEmail = ''
    emailLock = False
    localActive = False
    audioLock = False
    cameraLock = False
    cmdActive = False # Makes sure commandQueue is
                      # not edited simultaneously
    # Min distance to trigger intrusion (centimeter)
    #minDistance = 110.0 
    minDistance = 50
    localPID = 0
    
    # Time to sleep between checking email
    sleepEmailCheck = 10

    # Set GPIO Pins
    GPIO_TRIGGER = 25
    GPIO_ECHO = 12
    GPIO_LED_BLUE = 16
    GPIO_LED_RED = 20
    GPIO_DHT = 26
     
    # Setting up global pi camera hook
    #camera = PiCamera()

    ###############################################
    #                  Setup Pins                 #
    ###############################################

    #GPIO Mode (BOARD / BCM)
    GPIO.setmode(GPIO.BCM)

    # Disabling GPIO debug info from stdout
    GPIO.setwarnings(False)

    # Setup Ultrasonic module
    setupSR04()

    setupLeds()

    setupDHT()
    
    # Blink test
    #blinkNTimes(GPIO_LED_BLUE, 5)



    ###############################################
    #               Update Config                 #
    ###############################################
    try:
        updateConfig()
    except(BaseException):
        print("[!] Unable to update config")


    ###############################################
    #  Multiprocessing Remote & Local Functions   #
    ###############################################
    remoteModule = multiproc.Process(target=moduleRemote)

    try:
        remoteModule.start()
        #sleep(10)
        #exCmd.start()
        #executeCommand()
    except (KeyboardInterrupt):
        print("[+] Quitting gracefully")
        cleanup()
        exit(0)
    except (BaseException):
        print("[!] Unknown error occured")
        cleanup()
        exit(0)


    #remoteModule.terminate()
    #localModule.terminate()
    
    #scanContinuous()
    
    #executeCommand()


###############################################
#                  Cleanup                    #
###############################################
def cleanup():
    GPIO.cleanup()
    exit(0)


###############################################
#            Process Remote Command           #
###############################################
def moduleRemote():
    """
    Checks email for new remote commands & executes them
    """

    global commandQueue, whiteListedEmail, credentials, sleepEmailCheck

    while (True):
        msgList = readEmail(credentials[0], credentials[1]) 
        print("Number of new emails: %d" % len(msgList))

        if (msgList != []):
            for msg in msgList:
                if (msg[0] == whiteListedEmail):
                    commandQueue.append(msg[1].lower())

        executeCommand()
        sleep(sleepEmailCheck)


###############################################
#            Process Local Command            #
###############################################
def moduleLocal():
    """
    Uses ultrasonic module to detect intrusion
    """

    global audioList, GPIO_LED_RED

    multiproc.Process(target=scanContinuous).start()

    while (True):
        detectIntrusion()

        commandQueue.append('intrusion')
        
        multiproc.Process(target=blinkNTimes, \
                args=(GPIO_LED_RED, 5,)).start()

        path = '%s/%s' % (getcwd(), audioList[0])
        multiproc.Process(target=playAudio, args=(path,)).start()
        executeCommand()

        sleep(30)



###############################################
#                Command Queue                #
###############################################

def executeCommand():

   global credentials, whiteListedEmail, commandQueue, commandList


   if (len(commandQueue) != 0):
       for i in range(len(commandQueue)):

           cmd = commandQueue.pop(0)
           print("Command: %s" % cmd)

           if (cmd == 'snap'):
               blinkLEDBlue()
               captureImage()
               sendEmail(credentials[0], credentials[1], \
                   whiteListedEmail, 'Security Report', \
                   'Here you go!', \
                   ['/tmp/intrusion.jpg'])
           elif (cmd == 'intrusion'):
               blinkLEDRed()
               captureImage()
               sendEmail(credentials[0], credentials[1], \
                   whiteListedEmail, 'Security Report', \
                   'WARNING: Intrusion detected!', \
                   ['/tmp/intrusion.jpg'])
           elif ( 'text' in cmd):
               speech = cmd.lstrip('text').strip()
               speakText(speech)
               blinkLEDBlue()
           elif ( cmd == 'quote'):
               speakRandomQuote()
               blinkLEDBlue()
           elif ( cmd == 'disarm'):
               print("Inside exCommand()")
               disarm()
           elif ( cmd == 'arm'):
               arm()
           elif ( cmd == 'status'):
               result = checkDHT()
               tmp = ("Temperature: %d\tHumidity: %d" % (result[1], \
                       result[0]))

               sendEmail(credentials[0], credentials[1], \
                   whiteListedEmail, 'Security Report', tmp)
           else:
               return






###############################################
#               Setup Functions               #
###############################################

def setupLeds():
    """
    Setup Leds 
    """
    global GPIO_LED_BLUE, GPIO_LED_RED

    #set GPIO direction (IN / OUT)
    GPIO.setup(GPIO_LED_BLUE, GPIO.OUT)
    GPIO.setup(GPIO_LED_RED, GPIO.OUT)


def setupSR04():
    """
    Setup Ultrasonic sensor
    """
    
    global GPIO_TRIGGER, GPIO_ECHO
    
     
    #set GPIO direction (IN / OUT)
    GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
    GPIO.setup(GPIO_ECHO, GPIO.IN)



###############################################
#                  DHT Sensor                 #
###############################################

def setupDHT():
    global sensorDHT

    sensorDHT = DHT.DHT11

def checkDHT():
    global sensorDHT, GPIO_DHT

    humidity, temp = DHT.read_retry(sensorDHT, GPIO_DHT)

    return (humidity, temp)


###############################################
#               Text to Speech                #
###############################################

def speakText(txt=''):

    if ( txt != ''):
        command = 'espeak -v english-mb-en1 -s140 -w /tmp/audio.wav "%s" \
                && mpv /tmp/audio.wav' % (txt)

        checkAudioLockState()
        acquireAudioLock()
        blinkLEDBlue()
        system(command)
        releaseAudioLock()


def speakRandomQuote(offensive=False):
    quote = ""

    if (offensive):
        quote = "".join(popen("fortune -o").readlines()).strip()
    else:
        quote = "".join(popen("fortune").readlines()).strip()

    blinkLEDBlue()
    speakText(quote)
        

###############################################
#                    Audio                    #
###############################################

def playAudio(filePath=''):
    """
    Play audio using mpv
    """

    if (filePath != ''):
        command = 'mpv %s' % (filePath)
        checkAudioLockState()
        acquireAudioLock()
        blinkLEDBlue()
        system(command)
        releaseAudioLock()
        
def checkAudioLockState():
    """
    Returns only when audio resource is not in a locked state
    """
    global audioLock

    while (audioLock == True):
        sleep(1)

    return

def acquireAudioLock():
    global audioLock
    audioLock = True

def releaseAudioLock():
    global audioLock
    audioLock = False

###############################################
#                  Pi Camera                  #
###############################################

def captureImage(timeFrame=1):

    camera = PiCamera()
    #checkCameraLockState()
    #acquireCameraLock()
    camera.start_preview()
    sleep(timeFrame)
    camera.capture('/tmp/intrusion.jpg')
    camera.stop_preview()
    camera.close()
    #releaseCameraLock()


def captureVideo(timeFrame=5, fileName='/tmp/intrusion.h264'):
    camera = PiCamera()
    #checkCameraLockState()
    #acquireCameraLock()
    camera.start_preview()
    camera.start_recording(fileName)
    sleep(timeFrame)
    camera.stop_recording()
    camera.stop_preview()
    camera.close()
    #releaseCameraLock()


###############################################
#               Bluetooth Sensor              #
###############################################

def scan():
    device = btscan(duration=5, lookup_names=False)
    return device

def scanContinuous():
    """
    Disarms localModule upon detection of whitelisted BT Device
    """
    
    global commandQueue

    while (True):
        if (verifyBTDevice() == True):
            #disarm()
            print("Disarm requrest via Bluetooth Verification")
            commandQueue.append('disarm')
            print(commandQueue)
            executeCommand()
            break
        else:
            sleep(5)

def verifyBTDevice():
    """
    Returns a boolean value indicating whether 
    a whitelisted device has been discovered
    in proximity
    """
    global whiteListedBTDevice
    result = scan()

    if ( result != []):
        for device in result:
            if (device == whiteListedBTDevice):
                return True

    return False

    
###############################################
#               Ultrasonic Sensor             #
###############################################

def detectIntrusion():
    global minDistance, audioList

    #try:
    while (True):

        dist = distance()

        print ("Measured Distance = %.1f cm" % dist)

        if ( dist <= minDistance):
            #print("Intrusion detected!")
            break
        else:    
            sleep(0.5)
 
    #except BaseException:
    #    print("[!] Bug caught in Ultrasonic module")


def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)
 
    # set Trigger after 0.01ms to LOW
    sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
 
    StartTime = time()
    StopTime = time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime

    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
 
    return distance
 


###############################################
#               Led Functions                 #
###############################################

def toggleLed(pinNumber=1):
    GPIO.output(pinNumber, 1)


def blinkLed(pinNumber=1):
    GPIO.output(pinNumber, True)
    sleep(0.5)
    GPIO.output(pinNumber, False)


def blinkNTimes(pinNumber=1, n=0, blinkFast=True):
    """
    Blink Led specified by the pinNumber n number of times
    If n=0, blink indefinitely
    """
    blinkTime = 0.5

    if ( blinkFast == False):
        blinkTime = 1.5
    
    if (n == 0):
        while (True):
            blinkLed(pinNumber)
            sleep(blinkTime)
    else:
        for i in range(n):
            blinkLed(pinNumber)
            sleep(blinkTime)


def blinkLEDRed():
    multiproc.Process(target=blinkNTimes, \
            args=(GPIO_LED_RED, 5,)).start()


def blinkLEDBlue():
    multiproc.Process(target=blinkNTimes, \
        args=(GPIO_LED_BLUE, 5, True,)).start()


###############################################
#                 Email Stuff                 #
###############################################

def updateConfig():
    """
    1st line: bot email address
    2nd line: bot email password
    3rd line: white listed email where the email will be sent
    4th line: white listed blueooth HW ID
    """

    global credentials, whiteListedEmail, whiteListedBTDevice, \
            userDataFile
    
    try:
        fp = open(userDataFile, 'r')
        user = fp.readline().strip()
        pwd = fp.readline().strip()
        whiteListedEmail = fp.readline().strip()
        whiteListedBTDevice = fp.readline().strip()
        fp.close()
    except (BaseException):
        print("[!] Unable to get user credentials")
        exit(1)

    credentials = (user, pwd)


def sendEmail(user='', pwd='', recipient='', subject='', \
        text='', attach=[]):

    """
    Precondition: Assumes user, pwd & recipient are always required

    attach = List of filenames we want to attach
    """
    

    if (user == '' or pwd == '' or recipient == ''):
        return 1
    
    checkEmailLockState()
    acquireEmailLock()

    msg = MIMEMultipart()
     
    msg['From'] = user
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
     
    msg.attach(MIMEText(text))
    
    if attach != []:
        for f in attach:
            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=basename(f)
                )
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user, pwd)
    server.sendmail(user, recipient, msg.as_string())
    server.quit()

    releaseEmailLock()


def readEmail(user='', pwd=''):
    if ( user == '' or pwd == ''):
        return 1

    checkEmailLockState()
    acquireEmailLock()

    msgList = []

    pop_conn = poplib.POP3_SSL('pop.gmail.com')
    pop_conn.user(user)
    pop_conn.pass_(pwd)

    messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
    
    messages = [b"\n".join(mssg[1]) for mssg in messages] 
    messages = [message_from_bytes(mssg) for mssg in messages] 
    
    for message in messages:
        tmpTuple = (extractSenderEmail(message['from']), \
                message['subject'])
        msgList.append(tmpTuple)

    pop_conn.quit()

    releaseEmailLock()

    return msgList


def extractSenderEmail(sender=''):
    if ( sender != ''):
        return sender.split('<')[1].replace('>','').strip()
    else:
        return 1


def checkEmailLockState():
    """
    Returns only when email resource is not in locked state
    """

    while (True):
        global emailLock
        if (emailLock == False):
            break
        else:
            sleep(1)


def acquireEmailLock():
    global emailLock

    emailLock = True


def releaseEmailLock():
    global emailLock

    emailLock = False


###############################################
#                 Security State              #
###############################################

def disarm(speak=True):
    global localModule, localActive, localPID

    print("Inside disarm()")
    try:
        if (localActive == True):
            localModule.terminate()

        if (localPID != 0):
            killPID = "kill -9 %d" % (localPID)
            print("Kill command: %s" % killPID)
            system(killPID)
    except (BaseException):
        print("[!] Exception caught while trying to kill localModule")
        
    localActive = False
    localPID = 0

    if (speak):
        speakText("Access granted. Security disabled.")

def arm():
    global localModule, localActive, localPID 

    try:
        if (localActive == False):
            localModule = multiproc.Process(target=moduleLocal)
            localModule.start()
            localActive = True
            localPID = localModule.pid
            speakText("Security enabled. Intrusion will be detected!")
    except(BaseException):
        print("[!] Unable to start local module")


if __name__ == '__main__':
    main()
