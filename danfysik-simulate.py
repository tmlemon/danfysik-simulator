"""
Created Thu Jul 12 14:42:11 2018
@author: tlemon

Program acts a simulated Danfysik power supply for Hall C PLC development
tasks.

Development of Python code uses second program run on a second computer
to send serial commands to PC running Python program. 
LabVIEW program at O:\DSG\Tyler\C\python\serial-writer.vi can be used
NI MAX VISA test panel can also be used.


commands needed
WA ######
W1 ##
N
F
RS
PO -
PO +
REM
LOC
SOFF
ERRC
NASW
"""

import serial
import time
from time import sleep


def serialIntialize(port,timeout):
    try:
        ser = serial.Serial(port,timeout=timeout)
        sleep(1)
    except serial.serialutil.SerialException:
        print('error')
        sleep(1)
        ser = serial.Serial(port,timeout=timeout)
        ser.close()
        #sleep(0.1)
        ser = serial.Serial(port,timeout=timeout)
    return ser


   
#%%
#sets up initial conditions for simulated power supply.
ser = serialIntialize('COM1',0.25)
state = ['ready']
dt = 1 #sec
slew = 1 #A/sec
current = 0 #A
iTarget = 0 #A
count = 0
cmd = ''
t0 = time.time()

#Loop constantly reads serial line until a command of 'STOP' is recieved.
# STOP condition coded into loop for development, will be removed and replaced
# with condiction that fits PLC.
while cmd.strip() != 'STOP':
    print(count)    
    print(state)
    print('current =',current)
    print('ramp rate =',slew)
    print('target =',iTarget)
    print()

    try:
        cmd = ser.read(15).decode()
    
        
        #sets up state list for actions to take when commands are recieved.    
        if cmd != '':
            #Stop condititon, closes serial comms and stops loop.
            if cmd.strip() == 'STOP':
                    print('Closing comms')
            #Sets up state to ramp magnet
            elif 'WA' in cmd:
                for i,element in enumerate(state):
                        if element == 'ready':
                            state.remove('ready')
                if 'ramping' not in state:
                    state.append('ramping')
                if cmd != '':            
                    iTarget = float(cmd[3:].strip())            
                margin = iTarget*0.01
            #changes ramp rate
            elif 'W1' in cmd:
                for i,element in enumerate(state):
                        if element == 'ready':
                            state.remove('ready')
                state.append('change slew')
                if cmd != '':
                    slewTarget = float(cmd[3:].strip())              
            else:
                print('error; unknown command')
    
    
        #ramps magnet to set current
        if current != iTarget and 'ready' not in state:# and 'ramping' in state:                
            if iTarget-margin <= current <= iTarget+margin:
                for element in state:
                    if element == 'ramping':
                        state.remove('ramping')        
            elif iTarget > current:
                if abs(iTarget - current) < 1:
                    current += slew*dt*0.25
                else:
                    current += slew*dt
            elif iTarget < current:
                if abs(iTarget - current) < 1:
                    current -= slew*dt*0.25
                else:
                    current -= slew*dt  
            else:
                print('error: ramp error')     
        #changes ramp/slew rate of magnet
        if 'change slew' in state and 'ready' not in state \
        and 'ramping' not in state:
            slew = slewTarget
            state.remove('change slew')
        #checks state list and declares PS ready if no other states are present.
        if len(state) == 0:
            state.append('ready')
        
        
        I = 'I'+str(current)+'\r'
        ser.write(I.encode())
       
        sleep(0.75)
        t1 = time.time()
        dt = t1 - t0
        t0 = t1
        count += 1
    
    except KeyboardInterrupt:
        print('User Stop')
        cmd = 'STOP'         
ser.close()


if ser.is_open == False:
    print('Comms closed.')
else:
    print('Error')
    ser.close

#%%
ser.close()