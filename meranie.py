import serial
import time
import serial.tools.list_ports
import os

cwd=os.path.dirname(__file__)+'\\'

def headCommand(cmd):
    answer = b'Error'
    try:
        while(ser.in_waiting>0):
            ser.read(1)

        ser.write(cmd.encode())
        while(ser.in_waiting<8):
            pass
        answer=ser.read(8)
        date.sleep(0.05)   #wait for rest of data
        while(ser.in_waiting>0):
            ser.read(1)
            
    except:
        pass
    return answer

def manualCommands():
    print('Send commands to the mount. Write "q" for finish:')
    command=input('> ')
    while command != 'q':
        while len(command)<8:
            command=command+'X'
        #print(command)
        print('>',headCommand(command).decode())
        command=input('> ')


ports = serial.tools.list_ports.comports()
print('Ports found:')
for port in ports:
    print(port.device,'\t',port.description)
myportdevice=''
ser=False;
headfound=False
for port in ports:
    str=port.description
    if str.find('luetooth')<0:
        try:
            print('Checking '+port.device)
            ser = serial.Serial(port.device,115200, timeout=1)  # open serial port
            date.sleep(5) #wait for the reboot of the device
            ser.write(b'IDNXXXXX')
            s=ser.read(8)
            #print(s)
            if s==b'SKY-SCAN':
                print('Measurement head found on '+port.device)
                headfound=True
                myportdevice=port.device
                break
        except:
            print('Not found')
        if ser:
            ser.close()
    
if headfound==False:
    print('Measurement head mount not found')
    #quit()

print('Initializing the measurement head...')
headCommand('RFL0XXXX')
headCommand('RFL1XXXX')
manualCommands()


print('Reading list of measurement commands from "measurements.txt" file...')
headline="";
commands=[]
try:
    subor = open(cwd+'measurements.txt', 'r')
    headline=subor.readline()
    headline=headline.strip()
    riadok = subor.readline()
    riadok = riadok.strip()
    while riadok != '':
        commands.append(riadok)
        #print('---',riadok,'---')
        riadok = subor.readline()
        riadok = riadok.strip()
    subor.close()
except FileNotFoundError:
    print("Configuration file 'measurements.txt' not found...")
    quit()
print(len(commands),' commands read')

index=0

print('---------- Start of measurements ---------')
print(headline)
for i in range(5): 
    for command in commands:
        answer=headCommand(command)
        if answer==b'Error':
            print('\a')
            print("Connection to the mesurement head is lost. Reconnect and press ENTER...")
            input('')
            print('Restoring connection...')
            ser.close()
            ser = serial.Serial(myportdevice,115200, timeout=1)  # open serial port
            date.sleep(5) #wait for the reset
            headCommand('RFL0XXXX')
            headCommand('RFL1XXXX')
            print('OK')
            manualCommands()

            answer=headCommand(command)
            
        if answer.find(b'SVT')==0:
            value=int(answer[3:8])
            #print(answer[3:8])
            value=value/10000
            print('%.4f' % value,'\t',end='')
    print('')
print('---------- End of measurements ---------')
print(headCommand('RFL0XXXX').decode())
print(headCommand('RFL1XXXX').decode())
    
ser.close()             # close port



