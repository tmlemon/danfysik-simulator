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

   
#%%
#sets up initial conditions for simulated power supply.
ser = serialIntialize('COM1',1)

#intial conditions on start up of simulated MPS
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
                for i,element in enumerate(state):
                        if element == 'ready':
                            state.remove('ready')
                state.append('change control')
                ctrlState = cmd
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
                    iTarget = float(cmd[3:].strip())*polarity
                    #margin = 0.001
                
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
        if abs(iTarget-current) > 0.001 and 'ready' not in state \
        and 'LOCAL' not in state and 'ramping' in state:
            #extra cases within allow adjustment of ramp interval to more
            #precisely reach set current.        
            if abs(iTarget - current) < 0.005:
                delta = slew*dt*0.001
            elif abs(iTarget - current) < 0.05:
                delta = slew*dt*0.01
            elif abs(iTarget - current) < 0.25:
                delta = slew*dt*0.1
            elif abs(iTarget - current) < 1:
                delta = slew*dt*0.25
            else:
                delta = slew*dt
                
            if iTarget > current:
                current += delta
            elif iTarget < current:
                current -= delta
            else:
                print('error: ramp error')     
        elif abs(iTarget-current) <= 0.001 and 'ready' not in state \
        and 'LOCAL' not in state and 'ramping' in state:
            for element in state:
                if element == 'ramping':
                    state.remove('ramping')

        #changes ramp/slew rate of magnet
        if 'change slew' in state and MPSNotReady:
            slew = slewTarget
            state.remove('change slew')
        
        #changes polarity of magnet
        if 'change polarity' in state and MPSNotReady:
            if polTarget == '+':# and iTarget <= 0:
                polarity = 1
            elif polTarget == '-':# and iTarget > 0:
                polarity = -1                
            iTarget = abs(iTarget)*polarity
            state.remove('change polarity')
            state.append('ramping')       
        
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
        print('status =',state)
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
        print(error)
        cmd = 'STOP'
ser.close()

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