from arduino import CANFrame
from cPickle import dump, load
from time import sleep
from time import time
from gzip import GzipFile

class LogSource(object):
    def __init__(self, filename, ratelimit=None):
        self.log = GzipFile(filename, "rb")
        self.interval = 1.0/ratelimit if ratelimit else 0
    def __iter__(self):
        last_returned = time() - self.interval
        while True:
            try:
                frame = load(self.log)
                elapsed = time() - last_returned
                sleep(max(self.interval - elapsed, 0))
                last_returned = time()
                yield frame
            except EOFError:
                return

class LogSink(object):
    def __init__(self, filename):
        self.log = GzipFile(filename, "wb")
        self.writes_since_flush = 0
    def writeFrame(self, frame):
        dump(frame, self.log, -1)
        self.writes_since_flush += 1
        if self.writes_since_flush == 1024:
            self.writes_since_flush = 0
            self.log.flush()
