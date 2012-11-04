import numpy as np
from struct import unpack
from collections import namedtuple
from time import time
from sys import stderr

_CANFrame_base = namedtuple('CANFrame',
        ['sentinel_start', 'sequence', 'id', 'rtr', 'length', 'data', 'crc',
         'valid_crc'])

class CANFrame(_CANFrame_base):
    def __str__(self):
        return "id=%04x, ts=%09d, seq=%07d, data=%s" % (self.id, self.sender_timestamp, self.sequence,
            " ".join("%02x" % x for x in self.data[:self.length]))


_atm_crc8_table = [
    0x00, 0x07, 0x0E, 0x09, 0x1C, 0x1B, 0x12, 0x15,
    0x38, 0x3F, 0x36, 0x31, 0x24, 0x23, 0x2A, 0x2D,
    0x70, 0x77, 0x7E, 0x79, 0x6C, 0x6B, 0x62, 0x65,
    0x48, 0x4F, 0x46, 0x41, 0x54, 0x53, 0x5A, 0x5D,
    0xE0, 0xE7, 0xEE, 0xE9, 0xFC, 0xFB, 0xF2, 0xF5,
    0xD8, 0xDF, 0xD6, 0xD1, 0xC4, 0xC3, 0xCA, 0xCD,
    0x90, 0x97, 0x9E, 0x99, 0x8C, 0x8B, 0x82, 0x85,
    0xA8, 0xAF, 0xA6, 0xA1, 0xB4, 0xB3, 0xBA, 0xBD,
    0xC7, 0xC0, 0xC9, 0xCE, 0xDB, 0xDC, 0xD5, 0xD2,
    0xFF, 0xF8, 0xF1, 0xF6, 0xE3, 0xE4, 0xED, 0xEA,
    0xB7, 0xB0, 0xB9, 0xBE, 0xAB, 0xAC, 0xA5, 0xA2,
    0x8F, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9D, 0x9A,
    0x27, 0x20, 0x29, 0x2E, 0x3B, 0x3C, 0x35, 0x32,
    0x1F, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0D, 0x0A,
    0x57, 0x50, 0x59, 0x5E, 0x4B, 0x4C, 0x45, 0x42,
    0x6F, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7D, 0x7A,
    0x89, 0x8E, 0x87, 0x80, 0x95, 0x92, 0x9B, 0x9C,
    0xB1, 0xB6, 0xBF, 0xB8, 0xAD, 0xAA, 0xA3, 0xA4,
    0xF9, 0xFE, 0xF7, 0xF0, 0xE5, 0xE2, 0xEB, 0xEC,
    0xC1, 0xC6, 0xCF, 0xC8, 0xDD, 0xDA, 0xD3, 0xD4,
    0x69, 0x6E, 0x67, 0x60, 0x75, 0x72, 0x7B, 0x7C,
    0x51, 0x56, 0x5F, 0x58, 0x4D, 0x4A, 0x43, 0x44,
    0x19, 0x1E, 0x17, 0x10, 0x05, 0x02, 0x0B, 0x0C,
    0x21, 0x26, 0x2F, 0x28, 0x3D, 0x3A, 0x33, 0x34,
    0x4E, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5C, 0x5B,
    0x76, 0x71, 0x78, 0x7F, 0x6A, 0x6D, 0x64, 0x63,
    0x3E, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2C, 0x2B,
    0x06, 0x01, 0x08, 0x0F, 0x1A, 0x1D, 0x14, 0x13,
    0xAE, 0xA9, 0xA0, 0xA7, 0xB2, 0xB5, 0xBC, 0xBB,
    0x96, 0x91, 0x98, 0x9F, 0x8A, 0x8D, 0x84, 0x83,
    0xDE, 0xD9, 0xD0, 0xD7, 0xC2, 0xC5, 0xCC, 0xCB,
    0xE6, 0xE1, 0xE8, 0xEF, 0xFA, 0xFD, 0xF4, 0xF3
]        

class ArduinoSource(object):
    PACKET_SIZE = 16
    SYNC_PACKETS = 2
    START_SENTINEL_VALUE = 0xAA
    FORMAT = "<BHH?BxxxxxxxxB"
    def __init__(self, portname, speed=250000):
        from serial import Serial
        port = Serial(baudrate=speed)
        try:
            from serial.win32 import DTR_CONTROL_DISABLE
            port.setDTR(DTR_CONTROL_DISABLE)
        except ImportError:
            print "Warning: Can't use DTR_CONTROL_DISABLE except under Windows"
            print
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
        (sentinel_start, sequence, can_id, rtr, length, crc) = \
                unpack(self.FORMAT, data)
        can_data = np.fromstring(data[7:15], dtype=np.uint8)[:length]
        valid_crc = self._verify_crc(data)
        return CANFrame(sentinel_start, sequence, can_id, rtr, length,
                        can_data, crc, valid_crc)

    def _verify_crc(self, data):
        initial = 0x00
        final = 0x55
        bytes = np.fromstring(data, dtype=np.uint8)
        crc = initial
        # Skip the CRC byte
        for byte in bytes[:-1]:
            crc = _atm_crc8_table[int(byte) ^ crc]
        return (crc ^ final) == bytes[-1]

    def _synchronize(self, reason=None):
        zeros = 0
        sync_start = time()
        errlog = open("errors.log", "a")
        if self.last_synced is not None:
            reason = reason or "unknown"
            errstr = "Lost sync (%s) after %d ms, " % (reason, (sync_start - self.last_synced)*1000)
            stderr.write(errstr)
            errlog.write(errstr)
        while zeros < self.PACKET_SIZE * self.SYNC_PACKETS:
            if ord(self.port.read()[0]) == 0:
                zeros += 1
            else:
                zeros = 0
        sync_end = time()
        self.last_synced = sync_end
        sync_time = sync_end - sync_start
        stderr.write("Took %d ms to regain sync\n" % (sync_time * 1000))
        errlog.write("Took %d ms to regain sync\n" % (sync_time * 1000))
        errlog.close()
        return

    def _is_sync_packet(self, packet):
        return all(ord(x) == 0 for x in packet) and len(packet) == self.PACKET_SIZE

    def _is_valid_frame(self, frame):
        return frame.sentinel_start == self.START_SENTINEL_VALUE and \
                 0 <= frame.length <= 8 and \
                 frame.valid_crc

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
                        "sentinel 0x%02X len 0x%02X valid crc %s" %
                        (frame.sentinel_start, frame.length, frame.valid_crc))
                    continue
                yield frame
