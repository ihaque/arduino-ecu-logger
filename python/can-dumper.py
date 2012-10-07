from functools import partial
from sys import argv
from sys import stdin
from time import time

from arduino import ArduinoSource
from text_log import TextSource
from binary_log import LogSink
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
    source = ArduinoSource("COM7")
    sinks = [CursesSink(25, 80), LogSink(argv[1])]
    try:
        map(partial(broadcast, sinks), source)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
