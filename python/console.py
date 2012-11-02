# Windows version of _curses at:
# http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses
import curses

from collections import defaultdict
from time import time

class CursesSink(object):
    def __init__(self, height=25, width=80):
        self.height = height
        self.width = width
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        #self.stdscr.resizeterm(height, width)

        self.ids_seen = []
        self.id2lastframe = {}
        self.id2arrivals = defaultdict(list)
        self.window_length = 256

    def writeFrame(self, frame):
        self.id2lastframe[frame.id] = frame
        arrivals = self.id2arrivals[frame.id]
        arrivals.append(time())
        if len(arrivals) > self.window_length:
            arrivals.pop(0)

        full_redraw = False
        if frame.id not in self.ids_seen:
            self.ids_seen.append(frame.id)
            self.ids_seen.sort()
            full_redraw = True

        if full_redraw:
            ids_to_draw = self.ids_seen[:self.height]
        elif self.ids_seen.index(frame.id) < self.height:
            ids_to_draw = [frame.id]
        else:
            ids_to_draw = []

        for id in ids_to_draw:
            row = self.ids_seen.index(id)
            frame = self.id2lastframe[id]
            arrivals = self.id2arrivals[id]
            if len(arrivals) == 1:
                rate = ""
            else:
                if (arrivals[-1] == arrivals[0]):
                    rate = "---"
                else:
                    fps = len(arrivals) / (arrivals[-1] - arrivals[0])
                    if fps < 1:
                        rate = "% 5d ms/frame" % (1000.0 / fps)
                    else:
                        rate = '%.1f' % fps
                        rate = "% 5s frame/sec" % rate
            datatext = "  ".join('%02X' % x for x in frame.data)
            datatext = datatext + (30 - len(datatext)) * " "
            text = "%04X\t%s\t%d\t%s\t%s" % \
                (frame.id, 'T' if frame.rtr else 'F', frame.length,
                datatext, rate)
            line = text + (self.width - len(text)) * " "
            self.stdscr.addstr(row, 0, line)

        self.stdscr.refresh()
        return

    def __del__(self):
        self.stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
