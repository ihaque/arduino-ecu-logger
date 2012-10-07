from serial import Serial
from serial.win32 import DTR_CONTROL_DISABLE
import numpy as np
from struct import unpack
from collections import namedtuple

CANFrame = namedtuple('CANFrame',
        ['sentinel_start', 'id', 'rtr', 'length', 'data', 'sentinel_end'])


class ArduinoSource(object):
    PACKET_SIZE = 14
    SYNC_PACKETS = 2
    SENTINEL_VALUE = 0xAA
    FORMAT = "<BH?BxxxxxxxxB"
    def __init__(self, portname, speed=115200):
        port = Serial(baudrate=115200)
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

    def _unpack_packet(self, data):
        (sentinel_start, can_id, rtr, length, sentinel_end) = \
                unpack(self.FORMAT, data)
        can_data = np.fromstring(data[5:13], dtype=np.uint8)[:length]
        return CANFrame(sentinel_start, can_id, rtr, length, can_data, sentinel_end)

    def _synchronize(self):
        zeros = 0
        while zeros < self.PACKET_SIZE * self.SYNC_PACKETS:
            if ord(self.port.read()[0]) == 0:
                zeros += 1
            else:
                zeros = 0
        return

    def _is_sync_packet(self, packet):
        return all(x == 0 for x in packet) and len(packet) == cls.PACKET_SIZE

    def _is_valid_frame(self, frame):
        return frame.sentinel_start == self.SENTINEL_VALUE and \
                 frame.sentinel_end == self.SENTINEL_VALUE

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
                    self._synchronize()
                    consecutive_syncs = 0
                    continue
                frame = self._unpack_packet(data)
                if not self._is_valid_frame(frame):
                    # Erroneous packet. We must have desynchronized.
                    self._synchronize()
                    continue
                yield frame
