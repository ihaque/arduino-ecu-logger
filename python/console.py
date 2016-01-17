# Windows version of _curses at:
# http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses
import curses

from collections import defaultdict
from time import time

from rx8 import RX8State

def right_pad(line, width):
    return line[:width] + (width - len(line)) * " "

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
        self.vehicle_state = RX8State()

    def writeFrame(self, frame):
        state_changed = self.vehicle_state.update(frame)
        self.id2lastframe[frame.id] = frame
        arrivals = self.id2arrivals[frame.id]
        arrivals.append(time())
        if len(arrivals) > self.window_length:
            arrivals.pop(0)

        full_redraw = True
        if frame.id not in self.ids_seen:
            self.ids_seen.append(frame.id)
            self.ids_seen.sort()
            full_redraw = True

        vehicle_state_lines = self.vehicle_state.to_string()
        n_header_lines = len(vehicle_state_lines) + 1
        if full_redraw:
            ids_to_draw = self.ids_seen[:self.height - n_header_lines]
        elif self.ids_seen.index(frame.id) < self.height - n_header_lines:
            ids_to_draw = [frame.id]
        else:
            ids_to_draw = []

        if state_changed or full_redraw:
            for i, line in enumerate(vehicle_state_lines):
                self.stdscr.addstr(i, 0, right_pad(line, self.width))
            self.stdscr.addstr(i + 1, 0, right_pad('', self.width))

        for id in ids_to_draw:
            row = self.ids_seen.index(id) + n_header_lines
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
            line = right_pad(text, self.width)
            self.stdscr.addstr(row, 0, line)

        self.stdscr.refresh()
        return

    def __del__(self):
        self.stdscr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
