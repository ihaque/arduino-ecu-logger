from serial import Serial
from serial.win32 import DTR_CONTROL_DISABLE
import numpy as np
from struct import unpack
from collections import namedtuple
from time import time
from sys import stderr

CANFrame = namedtuple('CANFrame',
        ['sentinel_start', 'sender_timestamp', 'sequence', 'id', 'rtr', 'length', 'data', 'sentinel_end'])


class ArduinoSource(object):
    PACKET_SIZE = 20
    SYNC_PACKETS = 2
    START_SENTINEL_VALUE = 0xAA
    END_SENTINEL_VALUE = 0x55 # unsigned ~0xAA
    FORMAT = "<BIHH?BxxxxxxxxB"
    def __init__(self, portname, speed=250000):
        port = Serial(baudrate=speed)
        try:
            port.setDTR(DTR_CONTROL_DISABLE)
        except ValueError:
            print "Warning: pySerial 2.6 under Windows is too old"
            print "You must use a newer rev to avoid resetting the board"
            print "upon connection"
            print
        port.port = portname
        port.open()
        self.port = port
        self.last_synced = None

    def _unpack_packet(self, data):
        (sentinel_start, sender_timestamp, sequence,
         can_id, rtr, length, sentinel_end) = \
                unpack(self.FORMAT, data)
        can_data = np.fromstring(data[11:19], dtype=np.uint8)[:length]
        return CANFrame(sentinel_start, sender_timestamp, sequence,
                        can_id, rtr, length, can_data, sentinel_end)

    def _synchronize(self, reason=None):
        zeros = 0
        sync_start = time()
        errlog = open("errors.log", "a")
        if self.last_synced is not None:
            reason = reason or "unknown"
            errstr = "Lost sync (%s) after %d ms, " % (reason, (sync_start - self.last_synced)*1000)
            #stderr.write(errstr)
            errlog.write(errstr)
        while zeros < self.PACKET_SIZE * self.SYNC_PACKETS:
            if ord(self.port.read()[0]) == 0:
                zeros += 1
            else:
                zeros = 0
        sync_end = time()
        self.last_synced = sync_end
        sync_time = sync_end - sync_start
        #stderr.write("Took %d ms to regain sync\n" % (sync_time * 1000))
        errlog.write("Took %d ms to regain sync\n" % (sync_time * 1000))
        errlog.close()
        return

    def _is_sync_packet(self, packet):
        return all(ord(x) == 0 for x in packet) and len(packet) == self.PACKET_SIZE

    def _is_valid_frame(self, frame):
        return frame.sentinel_start == self.START_SENTINEL_VALUE and \
                 frame.sentinel_end == self.END_SENTINEL_VALUE and \
                 0 <= frame.length <= 8

    def __iter__(self):
        self._synchronize()
        consecutive_syncs = 0
        while True:
            data = self.port.read(self.PACKET_SIZE)
            if self._is_sync_packet(data):
                consecutive_syncs += 1
                if consecutive_syncs == self.SYNC_PACKETS:
                    consecutive_syncs = 0
                continue
            else:
                if consecutive_syncs:
                    # Got a data frame after an incorrect number of
                    # sync packets. Better resynchronize.
                    self._synchronize("wrong # syncs")
                    consecutive_syncs = 0
                    continue
                frame = self._unpack_packet(data)
                if not self._is_valid_frame(frame):
                    # Erroneous packet. We must have desynchronized.
                    self._synchronize(
                        "sentinel 0x%02X 0x%02X len 0x%02X" %
                        (frame.sentinel_start, frame.sentinel_end, frame.length))
                    continue
                yield frame
