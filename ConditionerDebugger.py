import RPi.GPIO as GPIO
import time

#GPIO.HIGH = 1/True
#GPIO.LOW = 0/False

#pin numbers, not GPIO numbers
list = [12]
desiredLoad=3
io18=12
io19=35
io20=38
#list = [8, 10, 12, 11, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26]
#PINS doesnt work: 3, 5, 7, 28

def executePin(pin):#io18=pin 12, io19=35, io20=38
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pin, GPIO.OUT)
    print("PIN:", pin)
    for i in range(0,10):
        GPIO.output(pin, GPIO.HIGH)
        print("HIGH")
        time.sleep(1)

        GPIO.output(pin, GPIO.LOW)
        print("LOW")
        time.sleep(1)

for i in list:
    executePin(i)
    
GPIO.cleanup()

print("done")


def loadToControl(loadValue):
    """
    returns A,B,C values in a list for the specified load value (1.5,3, or 6)
    Non-valid loadvalues are automatically routed to the charger
"""
    if loadValue==1.5:
        ctrlA=1
        ctrlB=1
        ctrlC=1       
    if loadValue==3:
        ctrlA=1
        ctrlB=1
        ctrlC=0
    if loadValue==6:
        ctrlA=1
        ctrlB=0
        ctrlC=0
    else:
        ctrlA=0
        ctrlB=0
        ctrlC=0
        # B and C values are irrelevant
    return [ctrlA, ctrlB, ctrlC]

def configureRelays(): #io18=pin 12, io19=35, io20=38
    controlList=loadToControl(desiredLoad)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(io18, GPIO.OUT)
    GPIO.setup(io19, GPIO.OUT)
    GPIO.setup(io20,GPIO.OUT)
    GPIO.output(io18, controlList[0])
    GPIO.output(io19, controlList[1])
    GPIO.output(io20, controlList[2])

configureRelays()
