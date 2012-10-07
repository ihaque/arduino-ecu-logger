from serial import Serial
from serial.win32 import DTR_CONTROL_DISABLE
from time import time
import numpy as np
from struct import unpack
from collections import namedtuple
from sys import stdin
import platform

if platform.system() == "Windows":
    import msvcrt
else:
    import select

def kbhit():
    if platform.system() == "Windows":
        return msvcrt.kbhit()
    else:
        inrdy, _, __ = select.select([sys.stdin], [], [], 0.001)
        return len(inrdy) > 0

CANFrame = namedtuple('CANFrame', ['id', 'rtr', 'length', 'data'])


def messages(port):
    PACKET_SIZE = 12
    SYNC_PACKETS = 2
    msg_header_format = "<H?B"
    def synchronize():
        # Synchronize to the message frames
        consecutive_zeros = 0
        iters = 0
        print "Resynchronizing..."
        sync_start = time()
        while consecutive_zeros < PACKET_SIZE * SYNC_PACKETS:
            if ord(port.read()[0]) == 0:
                consecutive_zeros += 1
            else:
                consecutive_zeros = 0
            iters += 1
            if time() - sync_start > 1:
                print "Resynchronizing...(%d)" % iters
                sync_start = time()
        #print "Successfully synchronized!"

    def is_sync_packet(packet):
        return np.all(np.fromstring(packet, dtype=np.uint8) == 0)

    synchronize()
    consecutive_sync_packets = 0
    while True:
        packet = port.read(PACKET_SIZE)
        if is_sync_packet(packet):
            if not consecutive_sync_packets:
                #print "Discarding sync packet"
                pass
            consecutive_sync_packets += 1
            if consecutive_sync_packets == SYNC_PACKETS:
                consecutive_sync_packets = 0
            continue
        else:
            if consecutive_sync_packets:
                # Got a data frame after an incorrect number of
                # sync packets. Better resynchronize.
                synchronize()
                consecutive_sync_packets = 0
                continue
            (can_id, rtr, length) = unpack(msg_header_format, packet[:4])
            data = np.fromstring(packet[4:12], dtype=np.uint8)
            if length > 8 or length == 0:
                # Erroneous packet. We must have desynchronized.
                synchronize()
                continue
            data = data[:length]
            yield CANFrame(can_id, rtr, length, data)

def main():
    port = Serial(baudrate=115200)
    try:
        port.setDTR(DTR_CONTROL_DISABLE)
    except ValueError:
        print "Warning: pySerial 2.6 under Windows is too old"
        print "You must use a newer rev to avoid resetting the board"
        print "upon connection"
        print
    port.port = "COM7"
    port.open()
    cnt = 0
    for msg in messages(port):
        if msg.id == 0x04B0:
            print "%04X\t%s\t%d\t%s" % \
                (msg.id, 'T' if msg.rtr else 'F', msg.length,
                 "  ".join(map(lambda x: '%02X' % x, msg.data)))
        if kbhit():
            while kbhit():
                stdin.read(1)
            return

if __name__ == "__main__":
    main()
