from functools import partial
from sys import argv
from sys import stdin
from sys import stdout
from time import time

from arduino import ArduinoSource
from text_log import TextSource
from text_log import TextSink
from hdf5_log import HDF5Sink
from hdf5_log import HDF5Source
from console import CursesSink

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
    sinks = [CursesSink(25, 80)]
    try:
        for i, frame in enumerate(source):
            broadcast(sinks, frame)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
