from time import sleep
from time import time
from arduino import CANFrame

import numpy as np

class TextSource(object):
    def __init__(self, filename, ratelimit=None):
        self.log = open(filename, "rb")
        self.interval = 1.0/ratelimit if ratelimit else 0
    def __iter__(self):
        last_returned = time() - self.interval
        for line in self.log:
            id, rtr, length, data = line.strip().split("\t")
            id = int(id, 16)
            rtr = True if rtr == 'T' else False
            length = int(length)
            data = np.array([int(x, 16) for x in data.split()], dtype=np.uint8)
            frame = CANFrame(0xAA, id, rtr, length, data, 0xAA)

            elapsed = time() - last_returned
            sleep(max(self.interval - elapsed, 0))
            last_returned = time()
            yield frame

class TextSink(object):
    def __init__(self, file):
        self.file = file
    def writeFrame(self, frame):
        text = '%u\t%04X\t%s\t%d\t%s\n' % (frame.sequence,
                frame.id,
                'T' if frame.rtr else 'F',
                frame.length,
                "  ".join('%02X' % x for x in frame.data[:frame.length]))
        self.file.write(text)
        return
