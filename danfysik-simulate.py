"""
Created Thu Jul 12 14:42:11 2018
@author: tlemon

Program acts a simulated Danfysik power supply for Hall C PLC development
tasks.

Development of Python code uses second program run on a second computer
to send serial commands to PC running Python program. 
LabVIEW program at O:\DSG\Tyler\C\python\serial-writer.vi can be used
NI MAX VISA test panel can also be used.

V4 attempts to clean up code and make simulated MPS respond in the syntax of
the actual MPS.
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
        ser = serial.Serial(port,timeout=timeout)
    return ser

   
#%%
#sets up initial conditions for simulated power supply.
ser = serialIntialize('COM1',1)

state = ['ready']
dt = 1 #sec
slew = 1 #A/sec
current = 0 #A
iTarget = 0 #A
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
    sstring2 = str(current)+'\r'
    sstring3 = str(round(current,2))+'\r'
    sstring4 = str(round(current*0.0001,3))+'\r'
    sstring5 = str(polarity)+'\r'
    sstring6 = str(iTarget)+'\r'
    sstring7 = str(slew)+'\r'
    sstring8 = str(ctrlState)+'\r'
    sstring9 = str(state[0])+'\r'
        
    try:
        cmd = ser.read(15).decode().strip()        
        if cmd != '':
            #looks for command to put MPS in local or remote control mode
            if cmd == 'LOC' or cmd.strip() == 'REM':
                for i,element in enumerate(state):
                        if element == 'ready':
                            state.remove('ready')
                state.append('change control')
                ctrlState = cmd.strip()
            #Status readback commands that should always work, regardless of
            #control state.
            elif cmd == 'AD 8':
                ser.write(sstring2.encode())
            elif cmd == 'AD 0':
                ser.write(sstring3.encode())
            elif cmd == 'AD 2':
                ser.write(sstring4.encode())
            elif cmd == 'PO':
                ser.write(sstring5.encode())
            elif cmd == 'RA':
                ser.write(sstring6.encode())
            elif cmd == 'R3':
                ser.write(sstring7.encode())
            elif cmd == 'CMDSTATE':
                ser.write(sstring8.encode())
            elif cmd == 'S1':
                ser.write(sstring9.encode())
            
            #Only listen to/add commands to state if not in local mode.
            elif 'LOCAL' not in state:
                #Stop condititon, closes serial comms and stops loop.
                if cmd == 'STOP':
                        print('Closing comms')       
                #Sets up to ramp magnet
                elif 'WA' in cmd:
                    for i,element in enumerate(state):
                            if element == 'ready':
                                state.remove('ready')
                    if 'ramping' not in state:
                        state.append('ramping')
                    iTarget = float(cmd[3:].strip())            
                    margin = 0.005
                #changes ramp rate
                elif 'W1' in cmd:
                    for i,element in enumerate(state):
                        if element == 'ready':
                            state.remove('ready')
                    state.append('change slew')
                    slewTarget = float(cmd[3:].strip())                 
                #change polarity
                elif 'PO' in cmd and len(cmd) > 2:
                    for i,element in enumerate(state):
                        if element == 'ready':
                            state.remove('ready')
                        state.append('change polarity')
                    polTarget = cmd[3:].strip()               
                else:
                    print('error; unknown command')
            elif 'LOCAL' in state:
                print('in local control mode')
            else:
                print('control mode error')
            
        #boolean status to determine whether MPS is ready to receive new
        # commands.
        MPSNotReady = 'ready' not in state and 'ramping' not in state \
            and 'LOCAL' not in state

        #changes to local/remote control mode
        if 'change control' in state and 'ready' not in state \
        and 'ramping' not in state:
            state.remove('change control')
            if ctrlState == 'LOC':
                state.append('LOCAL')
            elif ctrlState == 'REM':
                state.remove('LOCAL')
                state.append('ready')
        #ramps magnet to set current
        if current != iTarget and 'ready' not in state \
        and 'LOCAL' not in state:
            #condition to see if MPS is ramped to current.
            if iTarget-margin <= current <= iTarget+margin:
                for element in state:
                    if element == 'ramping':
                        state.remove('ramping')        
            
            #condition for positive ramping
            #extra cases within allow adjustment of ramp interval to more
            #precisely reach set current.
            elif iTarget > current:
                if abs(iTarget - current) < 0.05:
                    current += slew*dt*0.01
                elif abs(iTarget - current) < 0.25:
                    current += slew*dt*0.1
                elif abs(iTarget - current) < 1:
                    current += slew*dt*0.25
                else:
                    current += slew*dt
            #condition for negative ramping.
            #extra cases within allow adjustment of ramp interval to more
            #precisely reach set current.
            elif iTarget < current:
                if abs(iTarget - current) < 0.05:
                    current -= slew*dt*0.01
                elif abs(iTarget - current) < 0.25:
                    current -= slew*dt*0.1
                elif abs(iTarget - current) < 1:
                    current -= slew*dt*0.25
                else:
                    current -= slew*dt
            else:
                print('error: ramp error')     
        #changes ramp/slew rate of magnet
        if 'change slew' in state and MPSNotReady:
            slew = slewTarget
            state.remove('change slew')
        #changes polarity of magnet
        if 'change polarity' in state and MPSNotReady:
            if polTarget == '+' and iTarget <= 0:
                polarity = 1
                iTarget = abs(iTarget)
            elif polTarget == '-' and iTarget > 0:
                polarity = -1
                iTarget = iTarget*-1
            state.remove('change polarity')
            state.append('ramping')       
        #checks state list and declares PS ready if no other states are present.
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
        print('status =',state)
        print()
        
        ser.write(('I'+str(current)).encode())        
        
        count += 1        
        t1 = time.time()
        dt = t1 - t0
        t0 = t1
    except KeyboardInterrupt:
        print('User Stop')
        cmd = 'STOP'
    except:
        print('ERROR')
        ser.close()
ser.close()

if ser.is_open == False:
    print('Comms closed.')
else:
    print('Error')
    ser.close

#%%
ser.close()
