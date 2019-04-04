#!/usr/bin/python

import json
import time
import math
from Adafruit_BNO055 import BNO055
import ConfigParser
import os

base_dir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

print "%s" % base_dir

# config file stuff
# Name of the file to store calibration data when the save/load calibration
# button is pressed.  Calibration data is stored in JSON format.
CALIBRATION_FILE = base_dir + '/calibration.json'
CONFIG_FILE = base_dir + '/level.conf'

# Start up web page stuff here...


roll_off = 0.0
pitch_off = 0.0
trailer_width_in = 96
trailer_length_in = 192
# Read the config file
def read_config():
    global roll_off
    global pitch_off
    global trailer_width_in
    global trailer_length_in

    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)
    try:
        roll_off = float(config.get("Adjust", "roll"))
        pitch_off = float(config.get("Adjust", "pitch"))
        trailer_width_in = int(config.get("Trailer", "width_in"))
        trailer_length_in = int(config.get("Trailer", "length_in"))
    except Exception as e:
        print("failed to read config file")
        pass
    print("roll_off %f pitch_off %f" % (roll_off, pitch_off))

# BNO interfaces
def init_bno():
    # open the BNO interface
    bno = BNO055.BNO055(serial_port='/dev/ttyS0', rst=18)
    # Initialize the BNO055 and stop if something went wrong.
    if not bno.begin():
        raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')
    return bno

def load_calibration(bno):
    # Try to Load calibration from disk.
    try:
        with open(CALIBRATION_FILE, 'r') as cal_file:
            data = json.load(cal_file)
        bno.set_calibration(data)
    except:
        print "Calibration file not found"
        pass
    return 'OK'

def save_calibration(bno):
    # Save calibration data to disk.
    data = bno.get_calibration()
    # Write the calibration to disk.
    with open(CALIBRATION_FILE, 'w') as cal_file:
        json.dump(data, cal_file)
    print "Calibration written"
    return 'OK'

arm_calibration = True
def process_calibration(bno):
    global arm_calibration
    sys, gyro, accel, mag = bno.get_calibration_status()
    if (arm_calibration and sys == 3 and gyro == 3 and accel == 3 and mag == 3):
        save_calibration(bno)
        arm_calibration = False
    else:
        print('System Cal info: Sys_cal={0} Gyro_cal={1} Accel_cal={2} Mag_cal={3}'.format(
                sys, gyro, accel, mag))


# level readings/processing
def process_level(bno):
    # We get heading, roll, pitch from the sensor
    #
    #            Z    X
    #            |   /
    #         ---|--/---
    #        / * | /   /|
    # Y ____/____|/   // 
    #      /         //
    #     /_________//
    #    |_________|/
    #
    #
    # heading is rotation around the Z Axis
    # roll is rotation around the X Axis
    # Pitch is rotation around the Y Axis
    #
    # The sensor is mounted in the trailer thusly
    #
    #                *
    #               / \
    #              /   \
    #             /     \
    #            /       \
    #        +---------------+
    #        |               |
    #        |       X       |
    #        |       |       |
    #        |       |       |
    #        |       |       |
    #        |       |       |
    #  Y ----|-------Z       |  (Z comes out toward user)
    #        |               |
    #        |               |
    #        |               |
    #        |               |
    #        |               |
    #        |               |
    #        +---------------+
    #
    # This means that rotation around the X axis "Roll" will be the level side
    # to side.  The rotation about the Y axis will be level from front to back (tounge
    # jack)
    #
    # And finally the rotation around the Z axis will be informational on which
    # way we are facing...  For fun!  :-D
    #

    # read in level
    heading, roll, pitch = bno.read_euler()

    # adjust
    roll = roll - roll_off
    pitch = pitch - pitch_off
    right_in = 0
    left_in = 0
    tounge_in = 0
    
    left_in = trailer_width_in * math.sin(math.radians(roll))
    if (left_in < 0):
        right_in = 0 - left_in
        left_in = 0
    
    tounge_in = trailer_width_in * math.sin(math.radians(pitch))
    
    print ("\n")
    if (roll_off != 0.0 or pitch_off != 0.0):
        print ("Adjusting roll %f and pitch %f deg" % (roll_off, pitch_off))

    print('Heading={0:0.2F} Roll={1:0.2F} Pitch={2:0.2F}'.format(heading, roll, pitch))
    print('width={0:0.2F}\" length={1:0.2F}\"'.format(trailer_width_in, trailer_length_in))
    print ("")
    print ("        (%02.1f)" % tounge_in)
    print ("           /\\")
    print ("          /  \\")
    print ("         /    \\")
    print ("        /      \\")
    print ("       /        \\")
    print ("      /          \\")
    print ("     /            \\")
    print ("    /              \\")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("")
    print ("(%02.1f)            (%02.1f)" % (left_in, right_in))
    print ("")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("    |              |")
    print ("    +--------------+")
    print ("")
    print ("")
    print ("   (%02.1f)" % heading)

# main running event loop
def main():
    bno = init_bno()
    if (os.path.isfile(CALIBRATION_FILE)):
        load_calibration(bno)

    while (1):
        read_config()
        process_calibration(bno)
        process_level(bno)
        time.sleep(1)

if (__name__ == "__main__"):
    main()

