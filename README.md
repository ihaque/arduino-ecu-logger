arduino-ecu-logger
==================

Arduino + CAN-BUS shield to monitor fuel consumption and other vehicle parameters. I first wrote this to get a fuel economy meter on my RX-8, and later worked to reverse engineer the messages streaming across the CAN-BUS to see what sensor data is available on the car.

Features:

1. Live streaming of CAN-BUS content over serial link to connected PC (with logging and viewing software on PC side)
2. Computes fuel consumption/mpg and displays on attached serial LCD
3. Dumps available OBD-II PIDs to microSD card

- [arduino-ecu-logger](#)
	- [Materials](#)
	- [Arduino side](#)
	- [PC side](#)
	- [The RX-8 CAN-BUS](#)

![screenshot](https://raw.githubusercontent.com/ihaque/arduino-ecu-logger/master/screenshot.png)

## Materials
1. Arduino Uno
2. [Serial LCD] (https://www.sparkfun.com/products/9394)
3. [CAN-BUS shield](https://www.sparkfun.com/products/13262) (includes a joystick and microSD slot)
4. [OBD-II to DB9 cable](https://www.sparkfun.com/products/10087) to connect between your car and the CAN shield
5. microSD card

## Arduino side
The Arduino can operate in one of four modes, selected on bootup using the joystick:

1. (down): live vehicle stats. Show MAF-based fuel efficiency (mpg) and consumption (oz/hr) on line 1 of LCD; coolant temperature and throttle position on line 2.
2. (up): CAN spy. Stream CAN-BUS frames over serial connection to attached PC for logging, reverse engineering, and analysis.
3. (left): query ECU for supported OBD-2 PIDs and write to microSD card.
4. (right): serial simulator. Send fake CAN-BUS frames over serial connection to test PC interface code.

Hardware pin connections are described in logger/README.

The PC interface uses a custom framing protocol for high-speed reliable transmission of CAN frames to the PC. Once every 127 frames, a synchronization frame is sent over the wire; each frame starts with a sentinel byte, and each frame is protected by a CRC8.

## PC side
python/can-dumper.py supports reading CAN frames either from a serial-connected Arduino (python/arduino.py:ArduinoSource) or from an on-disk log (python/hdf5_log.py:HDF5Source), and can stream frames simultaneously to a number of outputs, including an on-disk log or a curses-based live display of different CAN-BUS addresses.

The curses interface is shown below:
![screenshot](https://raw.githubusercontent.com/ihaque/arduino-ecu-logger/master/screenshot.png)

The top two rows are a summary of the vehicle's current state, as inferred from decoding data on the CAN-BUS (see section below on the RX-8). Below that is a live-updating view of the last frame received for each CAN-BUS destination ID, including the `rtr` and `data` fields, as well as an estimate of the rate at which traffic is flowing to each ID. Following these fields as inputs are changed on a car (eg, throttle position, rpm, brake engagement, speed, steering angle) can help decode their meaning.

## The RX-8 CAN

[This blog post](http://www.madox.net/blog/projects/mazda-can-bus/) describes some reverse engineering of CAN messages from a Mazda 3; much of the data is the same on my Mazda RX-8, but not all. The spreadsheet in data/ (as well as the decoding logic in python/rx8.py) describe the CAN IDs that I have successfully mapped on the RX-8. HDF5 logs can also be plotted using python/plot_logs.py.
