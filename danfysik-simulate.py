"""
Created Thu Jul 12 14:42:11 2018
@author: tlemon

Program acts a simulated Danfysik power supply for Hall C PLC development
tasks.

Development of Python code uses second program run on a second computer
to send serial commands to PC running Python program. 
LabVIEW program at O:\DSG\Tyler\C\python\serial-writer.vi can be used
NI MAX VISA test panel can also be used.
"""

import serial
import time
from time import sleep

#function intializess serial connection.
def serialIntialize(port,timeout):
    try:
        ser = serial.Serial(port,timeout=timeout)
        sleep(1)
    except:
        print('Intialization Error')
    return ser

#function to somewhat simplify code line for writing to serial and made it 
#more obvious what is being written.
def serialWrite(string):
    ser.write(string.encode())
    return 1


#%%
timing = 1

#sets up initial conditions for simulated power supply.
ser = serialIntialize('COM1',timing)

#intial conditions on start up of simulated MPS
state = ['ready']
dt = timing #sec
slew = 1 #A/sec
current = 0 #A
iTarget = 0 #A
margin = 0.001
polarity = 1
ctrlState = 'REM'
count = 0
cmd = ''
t0 = time.time()

#Loop constantly reads serial line until a command of 'STOP' is recieved.
# STOP condition coded into loop for development, will be removed and replaced
# with condiction that fits PLC.
while cmd != 'STOP':
    sstring0 = ''+'\r'
    sstring1 = ''+'\r'
    sstring2 = 'I'+str(current)+'\r'
    sstring3 = 'i'+str(round(current,2))+'\r'
    sstring4 = 'V'+str(round(current*0.0001,3))+'\r'
    sstring5 = 'P'+str(polarity)+'\r'
    sstring6 = 'T'+str(iTarget)+'\r'
    sstring7 = 'r'+str(slew)+'\r'
    sstring8 = 'c'+str(ctrlState)+'\r'
    sstring9 = 's'+str(state[0])+'\r'
        
    try:
        cmd = ser.read(15).decode().strip()        
        if cmd != '':
            #looks for command to put MPS in local or remote control mode
            if cmd == 'LOC' or cmd == 'REM':
                ctrlState = cmd
                if 'ready' in state:
                    state.remove('ready')
                if cmd == 'LOC' and 'LOCAL' not in state:
                    #case used for situations where already in local mode.
                    state.append('LOCAL')
                elif cmd == 'REM' and 'LOCAL' in state:
                    #case used for when already in remote mode.
                    state.remove('LOCAL')
                    state.append('ready')
            #Status readback commands that should always work, regardless of
            #control state.
            elif cmd == 'AD 8':
                serialWrite(sstring2)
            elif cmd == 'AD 0':
                serialWrite(sstring3)
            elif cmd == 'AD 2':
                serialWrite(sstring4)
            elif cmd == 'PO':
                serialWrite(sstring5)
            elif cmd == 'RA':
                serialWrite(sstring6)
            elif cmd == 'R3':
                serialWrite(sstring7)
            elif cmd == 'CMDSTATE':
                serialWrite(sstring8)
            elif cmd == 'S1':
                serialWrite(sstring9)
            #gives message if in local mode
            elif 'LOCAL' in state:
                print('in local control mode')
            #Only listen to/add commands to state if not in local mode.
            elif 'LOCAL' not in state:
                #Stop condititon, closes serial comms and stops loop.
                if cmd == 'STOP':
                        print('Closing comms')       
                #Sets up to ramp magnet. magnet ramp occurs in case after
                #intial message check.
                elif 'WA' in cmd:
                    if 'ready' in state:
                        state.remove('ready')
                    if 'ramping' not in state:
                        state.append('ramping')
                    iTarget = float(cmd[3:].strip())*polarity
                #changes ramp rate
                elif 'W1' in cmd and 'ready' in state:
                    state.remove('ready')
                    slew = float(cmd[3:].strip())
                #change polarity
                elif 'PO' in cmd and len(cmd) > 2 and 'ready' in state:
                    state.remove('ready')
                    if cmd[3:].strip() == '+':
                        polarity = 1
                    elif cmd[3:].strip() == '-':
                        polarity = -1
                    else:
                        print('polarity error')
                        polarity = 1
                    iTarget = abs(iTarget)*polarity
                    state.append('ramping')                    
                #message for action commands given when MPS is not ready
                elif cmd != '' and 'ready' not in state:
                    print('MPS not ready')
                #error condition for unknown commands
                else:
                    print('error; unknown command')
            
            #error error condition if somehow in a state other than REM or LOC
            else:
                print('control mode error')
            
        #ramps magnet to set current
        if abs(iTarget-current) > margin and 'ramping' in state \
        and 'LOCAL' not in state:
            #extra cases within allow adjustment of ramp interval to more
            #precisely reach set current.        
        
            '''
            2018-09-05
            NEED TO TEST CHANGES TO DELTAS BELOW
            '''
        
            if abs(iTarget - current) < slew*0.005:
                delta = dt*0.001
            elif abs(iTarget - current) < slew*0.05:
                delta = slew*dt*0.01    #0.0025
            elif abs(iTarget - current) < slew*0.25:
                delta = slew*dt*0.05 #0.05
            elif abs(iTarget - current) < slew*1:
                delta = slew*dt*0.2    #0.125
            else:
                delta = slew*dt
            #increments current to setpoint.
            if iTarget > current:
                current += delta
            elif iTarget < current:
                current -= delta
            else:
                print('error: ramp error')     
        elif abs(iTarget-current) <= margin and 'ready' not in state \
        and 'LOCAL' not in state and 'ramping' in state:
            state.remove('ramping')
        
        #checks state list and declares PS ready if no other states are present
        if len(state) == 0:
            state.append('ready')               

        print(count)    
        print('16-bit current =',current)
        print('current =',round(current,2))
        print('voltage =',round(current*0.0001,3))
        print('polarity =',polarity)
        print('ramp rate =',slew)
        print('target =',iTarget)
        print('control state =',ctrlState)
        print('status =',state[0])
        print()
        
        #ser.write(sstring2.encode())        
        
        count += 1        
        t1 = time.time()
        dt = t1 - t0
        t0 = t1
    except KeyboardInterrupt:
        print('User Stop')
        cmd = 'STOP'
    except Exception as error:
        raise
        cmd = 'STOP'
ser.close() # <-- if program hangs up during development using Spyder, put 
# cursor on this line and press F9.

if ser.is_open == False:
    print('Comms closed.')
else:
    print('Error; attempting to close comms again.')
    ser.close

#%%
#IF RUNNING IN IDE: if program hangs up or does not close properly,
# line of code below must be used to close serial communication before starting
# program again.
# IF RUNNING IN SPYDER: put cursor in cell and hit ctrl+ENTER
ser.close()