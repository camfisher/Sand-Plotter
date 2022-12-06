from tkinter import *
import tkinter.font as tkFont
import threading
from datetime import datetime
import time
import serial
import os, random
import math
import board
import neopixel
pixels = neopixel.NeoPixel(board.D18, 180)

INTERVAL = 1  # seconds between loops
VALID_DAYS = [0,1,2,3,4] # days of week to run program MONDAY TO FRIDAY
VALID_HOURS = (9, 19)  # (start, stop) hours 24 hour time
M_coord = [0,0] # machine coordinates global variable

#setup close action for if [X] button is pushed
def close():
    window.destroy()

#declare window
window = Tk()

#set window title
window.title("Sand Plotter")

#set window width and height
window.configure(width=window.winfo_screenwidth(), height=window.winfo_screenheight())
window.attributes('-fullscreen', True)

#set window background color
window.configure(bg='lightgray')

#setup close button
btn_close = Button(text="X", command = close)
btn_close.place(relx = 1.0, y = 0, anchor="ne")

#setup Coordinate Text
data = Button(justify = "center", text="Day: \nStart Time: \nCurrent file: ")
data["font"] = tkFont.Font(size = 40)
data.place(relx = 0.5, rely = 0.5, anchor = CENTER)

def GRBL_Wake(s):
    s.write("\r\n\r\n".encode())
    grbl_out = s.readline() # Wait for grbl to initialize
    #s.write("Ctrl-x".encode())
    s.flushInput()

def Home(s):
    s.write(('$H\n').encode())
    grbl_out = s.readline() # Wait for grbl response with carriage return
    grbl_out_str=str(grbl_out)
    #print('Homing : ' + grbl_out_str)
    s.write(('F1000\n').encode())
    grbl_out = s.readline() # Wait for grbl response with carriage return
    grbl_out_str=str(grbl_out)
    #print('Feedrate : ' + grbl_out_str)

def Gcode_send_next(s, line):
    #GRBL_Wake_Next(s)
    s.write(('F1000\n').encode()) # Prevents error due to sender idling between gcode statements
    grbl_out = s.readline() # Wait for grbl response with carriage return
    grbl_out_str=str(grbl_out)
    #print('Feedrate : ' + grbl_out_str)
    l = line.strip() # Strip all EOL characters for streaming
    s.write((l + '\n').encode()) # Send g-code block to grbl
    grbl_out = s.readline() # Wait for grbl response with carriage return
    #print(str(grbl_out))
    return(str(grbl_out))

def Day_to_Day():
    dt = datetime.now()
    switch={
        0:"Monday",
        1:"Tuesday",
        2:"Wednesday",
        3:"Thursday",
        4:"Friday",
        5:"Saturday",
        6:"Sunday"
        }
    return switch.get(dt.weekday(), "Invalid Day")

def Check_for_completion(s):
    s.write(('?\n').encode())
    grbl_out = s.readline()
    grbl_out_str=str(grbl_out)
    while(grbl_out_str.find("Idle") < 0):
        s.write(('?\n').encode())
        grbl_out = s.readline()
        grbl_out_str=str(grbl_out)
        #print(' : ' + grbl_out_str)

def GRBL_Sender():
    dt = datetime.now()

    # Open grbl serial port
    s = serial.Serial('/dev/ttyUSB0',115200)

    # Opens up a random G-Code File
    random_file = random.choice(os.listdir("/home/timcallinan/GCODE/"))
    file_path = os.path.join("/home/timcallinan/GCODE/", random_file)
    #file_path = ("corners.gcode")
    print(file_path)
    data.config(text=("AACC Mechatronics\nDay: " + Day_to_Day() +"\nStart Time: " + str(dt.hour) + ":" + str(dt.minute) + "\nFile:\n" + random_file))
    f = open(file_path,'r');

    # Wake up grbl
    GRBL_Wake(s)

    #Zerro Machine Coordinates
    M_coord = [0,0]
    M_next = [0,0]
    M_dist_to_next = 0.0

    # Home Machine
    Home(s)

    # Stream g-code to grbl
    for line in f:
        #send first gcode line
        grbl_out_str = Gcode_send_next(s, line)

    # Wait for gcode execute to complete
    Check_for_completion(s)

    # Close file and serial port
    f.close()
    s.close()

def check_program_window() -> bool:
    dt = datetime.now()
    print(dt.weekday())
    if dt.weekday() not in VALID_DAYS:
        return False  # not a valid day

    if VALID_HOURS[0] <= dt.hour and dt.hour <= VALID_HOURS[1]:
        return True
    else:
        return False

def start() -> None:
    while True:
        if check_program_window():
            #stuff to run 9am-7pm Mon-Sat
            print("sand pltter is running")
            GRBL_Sender()

#This just starts the program
if __name__ == "__main__":
    pixels.fill((255,255,255))
    plotter_thread = threading.Thread(target = start, daemon = True)

    plotter_thread.start()
    window.mainloop()
