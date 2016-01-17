arduino-ecu-logger
==================

Arduino + CAN-BUS shield to monitor fuel consumption and other vehicle parameters.

Features:
1. Live streaming of CAN-BUS content over serial link to connected PC (with logging and viewing software on PC side)
2. Computes fuel consumption/mpg and displays on attached serial LCD
3. Dumps available OBD-II PIDs to microSD card

![screenshot](https://raw.githubusercontent.com/ihaque/arduino-ecu-logger/master/screenshot.png)

## Materials
1. Arduino Uno
2. [Serial LCD] (https://www.sparkfun.com/products/9394)
3. [CAN-BUS shield](https://www.sparkfun.com/products/13262) (includes a joystick and microSD slot)
4. [OBD-II to DB9 cable](https://www.sparkfun.com/products/10087) to connect between your car and the CAN shield
5. microSD card

## Description
### Arduino side
The Arduino can operate in one of four modes, selected on bootup using the joystick:
1. (down): live vehicle stats. Show MAF-based fuel efficiency (mpg) and consumption (oz/hr) on line 1 of LCD; coolant temperature and throttle position on line 2.
2. (up): CAN spy. Stream CAN-BUS frames over serial connection to attached PC for logging, reverse engineering, and analysis.
3. (left): query ECU for supported OBD-2 PIDs and write to microSD card.
4. (right): serial simulator. Send fake CAN-BUS frames over serial connection to test PC interface code.

Hardware pin connections are described in logger/README.

The PC interface uses a custom framing protocol for high-speed reliable transmission of CAN frames to the PC. Once every 127 frames, a synchronization frame is sent over the wire; each frame starts with a sentinel byte, and each frame is protected by a CRC8.

### PC side
python/can-dumper.py supports reading CAN frames either from a serial-connected Arduino (python/arduino.py:ArduinoSource) or from an on-disk log (python/hdf5_log.py:HDF5Source), and can stream frames simultaneously to a number of outputs, including an on-disk log or a curses-based live display of different CAN-BUS addresses.

The curses interface is shown below:
![screenshot](https://raw.githubusercontent.com/ihaque/arduino-ecu-logger/master/screenshot.png)

