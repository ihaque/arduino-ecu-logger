from time import time
from sys import argv
from sys import stdin
from itertools import cycle

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


def main():
    #source = cycle(TextSource(argv[1], ratelimit=600))
    source = ArduinoSource("COM7")
    sinks = [CursesSink(25, 80), LogSink(argv[1])]
    for frame in source:
        for sink in sinks:
            sink.writeFrame(frame)
            if kbhit():
                while kbhit():
                    stdin.read(1)
                return


if __name__ == "__main__":
    main()
