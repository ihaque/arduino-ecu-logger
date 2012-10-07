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

