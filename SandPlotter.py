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
VALID_HOURS = (9, 24)  # (start, stop) hours 24 hour time

def GRBL_Wake(s):
    s.write("\r\n\r\n".encode())
    time.sleep(2)   # Wait for grbl to initialize
    s.flushInput()

def GRBL_Wake_for_Next(s):
    s.write("\r\n\r\n".encode())
    #time.sleep(.1)   # Wait for grbl to initialize
    grbl_out = s.readline()
    s.flushInput()

#get the distance between the current location and the commanded gcode location
def Dist_Next(Current, Next):
    #print("next X: " + Next[0] + "| next Y: " + Next[1])
    #print("Current X: " + Current[0] + "| Current Y: " + Current[1])
    distance = math.sqrt(math.pow((float(Next[0]) - float(Current[0])),2) + math.pow((float(Next[1]) - float(Current[1])), 2))
    #print("distance: " + "{:.2f}".format(distance))
    return distance

def Gcode_Parse(Gcode_Coords):
    M = [0,0]
    M[0] = Gcode_Coords[Gcode_Coords.find("X")+1 : Gcode_Coords.find("Y")]
    #print("GCode X: " + M[0])
    M[1] = Gcode_Coords[(Gcode_Coords.find("Y")+1):len(Gcode_Coords)]
    #print("GCode Y: " + M[1])
    print("Next Coordinates")
    print("X: " + M[0] + " |Y: " + M[1])
    return M
    
def MWC_Parse(MWC_Coords):
    MWC = [0,0]
    MWC_Coords = MWC_Coords[MWC_Coords.find("<"):(MWC_Coords.find(">")+1)]
    #print(MWC_Coords)
    MWC[0] = MWC_Coords[(MWC_Coords.find(":")+1):(MWC_Coords.find(","))]
    #print("Machine X: " + MWC[0])
    MWC[1] = MWC_Coords[((MWC_Coords.find(",")+1)):(MWC_Coords.find(",", MWC_Coords.find(",") + 1))]
    #print("Machine Y: " + MWC[1])
    return MWC

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
    GRBL_Wake(s)
    s.write(('F1000\n').encode())
    grbl_out = s.readline() # Wait for grbl response with carriage return
    grbl_out_str=str(grbl_out)
    l = line.strip() # Strip all EOL characters for streaming
    s.write((l + '\n').encode()) # Send g-code block to grbl
    grbl_out = s.readline() # Wait for grbl response with carriage return
    #print(str(grbl_out))
    return(str(grbl_out))
    
def Get_status(s):
    s.write(('?\n').encode())
    grbl_out = s.readline()
    grbl_out_str = str(grbl_out)
    while(grbl_out_str.find("ok") > 0 and grbl_out_str.find("WPos") < 0):
        #print(grbl_out_str)
        s.write(('?\n').encode())
        grbl_out = s.readline()
        grbl_out_str = str(grbl_out)
    return grbl_out_str

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
    
    # Open grbl serial port
    s = serial.Serial('/dev/ttyUSB0',115200)
     
    # Opens up a random G-Code File
    random_file = random.choice(os.listdir("/home/timcallinan/GCODE/"))
    file_path = os.path.join("/home/timcallinan/GCODE/", random_file)
    #file_path = ("corners.gcode")
    print(file_path)
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
            
        #set next coord
        M_next = Gcode_Parse(line.strip())
            
        #get current coordinates for starting while loop
        grbl_out_str = Get_status(s)
        
        #parse grbl output into x and y coordinates
        M_coord = MWC_Parse(grbl_out_str)
        
        #calculate distance between where the machine is to where it needs to be
        M_dist_to_next = Dist_Next(M_coord, M_next)
        
        #get distance between last (ish) coordinate and next coordinate
        M_start_dist = M_dist_to_next
        
        while(M_dist_to_next > M_start_dist * 0.8):
            grbl_out_str = Get_status(s)
            M_coord = MWC_Parse(grbl_out_str)
            #print(M_coord[0] + " | " + M_coord[1])
            M_dist_to_next = Dist_Next(M_coord, M_next)
            #print("X: " + M_coord[0] + " |Y: " + M_coord[1] + " |Target: X: " + str(M_next[0]) + " |Y: " + str(M_next[1]))
            #print("Distance To Next: " + "{:.2f}".format(M_dist_to_next))
            build(M_coord[0],M_coord[1])
        #while(grbl_out_str.find("Idle") < 0):
            #grbl_out_str = Get_status(s)
        
    # Wait for gcode execute to complete
    Check_for_completion(s)        
     
    # Close file and serial port
    f.close()
    s.close()



def run_program():
    #stuff to run 9am-7pm Mon-Sat
    print("sand pltter is running")
    GRBL_Sender()
    pass


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

    while True:  # keep program looping
        if check_program_window():
            run_program()

        time.sleep(INTERVAL)


#This just starts the program 
if __name__ == "__main__":
    pixels.fill((255,255,255))
    start()
    



