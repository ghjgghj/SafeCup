# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 13:57:47 2020

@author: Zhaorui
"""
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 12:50:54 2020

@author: Zhaorui
"""
import matplotlib.pyplot as plt
import pyfirmata
import time
import requests

TARGET_UPDATE = 50

# post request
payload = {
  "app_key": "FLTP9vbts14XbLvnX4i5",
  "app_secret": "s0iFiufY3pNdN0OcxatxenQFp5USOXKyqxMjHmgseg0uLsofycwB0w9TZbYmR9Lp",
  "target_type": "app",
  "content": "Someone might have tampered with your drink! "
}

# arduino  
board = pyfirmata.Arduino('COM4')
it = pyfirmata.util.Iterator(board)
it.start()

analog_input = board.get_pin('a:0:i')

THRESHOLD = 0.03 #ratio
THRESHOLD_LONG = 0.03

# Calibration 
r1 = [1000,2000,4700,10000,15000,100000,1000000]
pins = [13,12,11,10,9,8,7]
SAMPLE_COUNT = 20;

# set all pins as low and configure to input
for i in range(len(pins)):
    p = board.get_pin('d:{}:o'.format(pins[i]))
    p.write(0)
    p.mode=pyfirmata.INPUT

def averageVoltage():
    total = 0
    for i in range(SAMPLE_COUNT): 
        time.sleep(0.05)
        total += analog_input.read()
    return 5*total/SAMPLE_COUNT # 0 to 1

def calculateResistance(R1,V):
    # print(V)
    # time.sleep(0.3)
    return R1/(5/V-1)

def findRef():
    # loop through all resist, find the best pin to use
    minimum = 2.5
    R = 10000000
    pin = None
    for i in range(len(pins)):
        board.digital[pins[i]].mode=pyfirmata.OUTPUT
        board.digital[pins[i]].write(1)
        V = averageVoltage()
        board.digital[pins[i]].write(0)
        board.digital[pins[i]].mode=pyfirmata.INPUT
        diff = abs(V-2.5)
        # print('resistance with', r1[i], 'is', calculateResistance(r1[i],V))
        if (5.0 > V and diff < minimum):
            minimum = diff
            pin = i
            R = calculateResistance(r1[i],V)
    print("best pin is", pins[pin], 'with resistance of', r1[pin])
    print('measured resistance', R)
    return pin

def measure(pin):
    # measure resistance with given pin
    minimum = 2.5
    R = 10000000
    for i in range(len(pins)):
        board.digital[pin[i]].mode=pyfirmata.OUTPUT
        board.digital[pin[i]].write(1)
        V = averageVoltage()
        board.digital[pin[i]].write(0)
        board.digital[pin[i]].mode=pyfirmata.INPUT
        diff = abs(V-2.5)
        print('resistance with', r1[i], 'is', calculateResistance(r1[i],V))
        if (5.0 > V and diff < minimum):
            minimum = diff
            R = calculateResistance(r1[i],V)
    print("Resistance = " + str(R))
    return R 


ref_pin = findRef()
board.digital[pins[ref_pin]].mode=pyfirmata.OUTPUT
board.digital[pins[ref_pin]].write(1)
    
prev_R = R = calculateResistance(r1[ref_pin], averageVoltage())
# running two times for it to stablize
prev_R = R = calculateResistance(r1[ref_pin], averageVoltage())
data = []
counter = 0
target_R = prev_R
while True:
    R = calculateResistance(r1[ref_pin], averageVoltage())
    data.append(R)
    diff = R - prev_R
    target_diff = R - target_R
    if abs(diff/prev_R) > THRESHOLD or abs(target_diff/target_R) > THRESHOLD_LONG:
        r = requests.post("https://api.pushed.co/1/push", data=payload)
        print(r)
        # print(R, target_diff, diff)
    print(R)
    if counter % TARGET_UPDATE == 0:
        # update target
        target_R = R
    prev_R = R
    plt.plot(data)
    plt.ylabel('Resistance')
    plt.show()
    time.sleep(0.2)
    counter +=1
    