# Simple program for automatized measurements
# ver. 20.3.2020
# Frantisek Kundracik

import serial  # pip install pyserial  - in command prompt
import time
import serial.tools.list_ports
import tkinter as tk  # pip install tk  - in command prompt
from tkinter import filedialog
import os
import sys
import keyboard  # pip install keyboard  - in command prompt

cwd = os.path.dirname(__file__) + '\\'


def setIpanoPosition(vyska, azimut):
    global seripano
    try:
        command = ':01SSL+%s%s#' % (str((int)(100 * vyska)).zfill(5), str((int)(100 * azimut)).zfill(5))
        command = command.encode()  # prerobit na postupnot 8-bit znakov
        # print(command)
        seripano.write(command)  # move to the given position
        seripano.read(19)  # odpoveď
        time.sleep(0.1)  # aby sa montáž stihla rozbehnúť
        seripano.write(b':01GAS#')  # get current position and state
        answer = seripano.read(19)
        while answer[17] == ord('1'):  # kód jednotky - je v pohybe
            seripano.write(b':01GAS#')  # get current position and state
            answer = seripano.read(19)
        return (answer.decode)
    except:
        return ('Error')


def restoreConnection():
    global seripano
    global serhead
    print('\a')
    print("USB connection is lost. Reconnect and press ENTER...")
    input('')
    print('Restoring connection to iPANO mount...')
    seripano.close()
    seripano = serial.Serial(myipanoportdevice, 115200, timeout=1)  # open serial port
    print('OK')
    print('Restoring connection to the measurement head...')
    serhead.close()
    serhead = serial.Serial(myheadportdevice, 115200, timeout=1)  # open serial port
    time.sleep(5)  # wait for the reset
    print('Initializing the measurement head...')
    headCommand('RFL0XXXX')
    headCommand('RFL1XXXX')
    print('OK')
    readManualCommands()


def headCommand(cmd):
    answer = b'Error'
    try:
        while (serhead.in_waiting > 0):
            serhead.read(1)

        serhead.write(cmd.encode())
        while (serhead.in_waiting < 8):
            pass
        answer = serhead.read(8)
        time.sleep(0.05)  # wait for rest of data
        while (serhead.in_waiting > 0):
            serhead.read(1)
    except:
        pass
    return answer.decode()


def manualCommands():
    global cwd
    print('Send commands to the mount. Write "q" for finish:')
    subor = open(cwd + 'running_commands.txt', 'w')
    command = input('> ')
    while command != 'q':
        while len(command) < 8:
            command = command + 'X'
        # print(command)
        subor.write(command + '\n')
        print('>', headCommand(command))
        command = input('> ')
    subor.close()


def readManualCommands():
    global cwd
    print('Executing manual commands...')
    subor = open(cwd + 'running_commands.txt', 'r')
    command = subor.readline().strip()
    while command != '':
        headCommand(command)
        command = subor.readline().strip()
    subor.close()


root = tk.Tk()
root.withdraw()  # block main GUI window

myipanoportdevice = ''
myheadportdevice = ''
ports = serial.tools.list_ports.comports(include_links=False)
print('Ports found:')
for port in ports:
    print(port.device, '\t', port.description)
print('Searching for iPANO mount...')
seripano = False
iPANOfound = False
serhead = False
headfound = False
for port in ports:
    strport = port.description
    if strport.find('luetooth') < 0:
        try:
            print('Checking ' + port.device)
            seripano = serial.Serial(port.device, 115200, timeout=1)  # open serial port
            seripano.write(b':01INF#')
            s = seripano.read(11)
            if s == b':10INF3600#':
                print('iPANO mount found on ' + port.device)
                myipanoportdevice = port.device
                iPANOfound = True
                break
        except:
            print('Not found')
        if seripano:
            seripano.close()
if iPANOfound == False:
    print('iPANO mount not found')
    # quit()
print('Searching for the measurement head...')
for port in ports:
    strport = port.description
    if strport.find('luetooth') < 0:
        try:
            print('Checking ' + port.device)
            serhead = serial.Serial(port.device, 115200, timeout=1)  # open serial port
            time.sleep(5)  # wait for the reboot of the device
            serhead.write(b'IDNXXXXX')
            s = serhead.read(8)
            # print(s)
            if s == b'SKY-SCAN':
                print('Measurement head found on ' + port.device)
                headfound = True
                myheadportdevice = port.device
                break
        except:
            print('Not found')
        if serhead:
            serhead.close()

if headfound == False:
    print('Measurement head mount not found')
    # quit()

print('Initializing the measurement head...')
headCommand('RFL0XXXX')
headCommand('RFL1XXXX')

filename_out = ''
continue_meas = False
if os.path.isfile(cwd + 'running.txt'):
    answer = input('Last measurement was stopped unexpectedly. Continue? (y/n): ')
    if answer == 'y':
        continue_meas = True

if continue_meas == False:
    print('Moving to the start position...')
    setIpanoPosition(0, 0)

continue_no = 0
if continue_meas == True:
    file_run = open(cwd + "running.txt", "r")
    file_positions_path = file_run.readline().strip()
    file_measurements_path = file_run.readline().strip()
    filename_out = file_run.readline().strip()
    continue_no = int(file_run.readline().strip())
    file_run.close()
else:
    print('Select the file containing head positions...')
    file_positions_path = filedialog.askopenfilename(parent=root)  # parent=root - dialog on top
    print(file_positions_path)
    print('Select the file containing measurement commands...')
    file_measurements_path = filedialog.askopenfilename(parent=root)

print('Reading list of head positions from "', file_positions_path, '" file...')
positions = []
try:
    subor = open(file_positions_path, 'r')
    riadok = subor.readline()
    while riadok != '':
        cislo = riadok.split("\t")
        vyska = float(cislo[0].strip())
        azimut = float(cislo[1].strip())
        positions.append((vyska, azimut))
        riadok = subor.readline()
    subor.close()
except FileNotFoundError:
    print("Configuration file '", file_positions_path, "' not found...")
    quit()
print(len(positions), ' positions read')

print('Reading list of measurement commands "', file_measurements_path, '" file...')
headline = ""
commands = []
try:
    subor = open(file_measurements_path, 'r')
    headline = subor.readline()
    headline = headline.strip()
    riadok = subor.readline()
    riadok = riadok.strip()
    while riadok != '':
        commands.append(riadok)
        # print('---',riadok,'---')
        riadok = subor.readline()
        riadok = riadok.strip()
    subor.close()
except FileNotFoundError:
    print('Configuration file "', file_measurements_path, '" not found...')
    quit()
print(len(commands), ' commands read')

if (continue_meas == False):
    print('Choose the name of the output-file...')
    filename_out = filedialog.asksaveasfilename(parent=root)
    if filename_out == '':  # asksaveasfile return `None` if dialog closed with "cancel".
        filename_out = cwd + 'measurement.txt'
    fileout = open(filename_out, "w")
    fileout.close()  # clear the content of the file

if (continue_meas == True):
    readManualCommands()
else:
    manualCommands()

print('---------- Start of measurements ---------')
print('Press Ctrl to pause the measurement')
print('finished', 'vyska', 'azimut', headline)

if (continue_meas == False):
    buf = 'z.angle\tazimuth\t%s\n' % headline
    fileout = open(filename_out, "a")
    fileout.write(buf)
    fileout.close()

index = 0
answer = ''
for (vyska, azimut) in positions:
    if (index < continue_no):
        index += 1
        continue
    answer = setIpanoPosition(vyska, azimut)
    if (answer == 'Error'):
        restoreConnection()
        answer = setIpanoPosition(vyska, azimut)

    print(int(100.0 * (index + 1) / len(positions)), '%', vyska, azimut, end='\t')
    buf = '%.2f\t%.2f\t' % (90.0 - vyska, azimut)

    for command in commands:
        # check for key pressed: loop until another key pressed
        if keyboard.is_pressed('Ctrl'):
            print('\a')
            print('Paused, press Shift to continue...')
            keyboard.wait('Shift')
            print('Running again')
        answer = headCommand(command)
        if answer == 'Error':
            break
        if answer.find('SVT') == 0:
            value = int(answer[3:8])
            # print(answer[3:8])
            value = value / 10000
            print('%.4f' % value, '\t', end='')
            buf = buf + '%.4f\t' % (value)

    if (answer == 'Error'):
        restoreConnection()
        buf = '%.2f\t%.2f\t' % (90.0 - vyska, azimut)
        print(int(100.0 * (index + 1) / len(positions)), '%', vyska, azimut, end='\t')
        for command in commands:
            answer = headCommand(command)
            if (answer == 'Error'):
                print(
                    '\a\nRepeating problem with USB connection was detected. Check the cables and run the program again.')
                sys.exit()
            if answer.find('SVT') == 0:
                value = int(answer[3:8])
                # print(answer[3:8])
                value = value / 10000
                print('%.4f' % value, '\t', end='')
                buf = buf + '%.4f\t' % (value)

    if (answer != 'Error'):
        buf = buf + '\n'
        print('')
        fileout = open(filename_out, "a")
        fileout.write(buf)
        fileout.close()
        index += 1
        # Značka kam sme sa dostali
        subor = open(cwd + 'running.txt', 'w')
        subor.write(file_positions_path + '\n')
        subor.write(file_measurements_path + '\n')
        subor.write(filename_out + '\n')
        subor.write(str(index) + '\n')
        subor.close()

print('')
print('---------- End of measurements ---------')

if os.path.isfile(cwd + 'running.txt'):
    os.remove(cwd + 'running.txt')
if os.path.isfile(cwd + 'running_commands.txt'):
    os.remove(cwd + 'running_commands.txt')

print('Closing filters...')
print(headCommand('SFL000XX'))
print(headCommand('SFL100XX'))

print('Moving to the initial position...')
setIpanoPosition(0, 0)

print('Initializing the measurement head...')
print(headCommand('RFL0XXXX'))
print(headCommand('RFL1XXXX'))

seripano.close()  # close port
serhead.close()
