from functools import partial
from sys import argv
from sys import stdin
from sys import stdout
from time import time

from arduino import ArduinoSource

import platform
if platform.system() == "Windows":
    from msvcrt import kbhit
else:
    import select
    def kbhit():
        inrdy, _, __ = select.select([sys.stdin], [], [], 0.001)
        return len(inrdy) > 0


def check_keyboard():
    if kbhit():
        while kbhit():
            stdin.read(1)
        raise KeyboardInterrupt
    return


def broadcast(sinks, frame):
    for sink in sinks:
        sink.writeFrame(frame)
        check_keyboard()
    return


def main():
    source = ArduinoSource("COM7", speed=115200)
    start = time()
    last_seq = None
    try:
        for i, frame in enumerate(source):
            if last_seq is not None:
                if ((frame.sequence - last_seq) & 0xFFFF) != 1:
                    print "Out-of-sequence detected at t=%.2f sec: %d, %d" % \
                            (time() - start, last_seq, frame.sequence)
            else:
                print "Started receiving packets"
            if i % 10000 == 0:
                print "Frame", i
            last_seq = frame.sequence
            check_keyboard()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
