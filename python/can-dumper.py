from serial import Serial
from serial.win32 import DTR_CONTROL_DISABLE
from time import time
import numpy as np
from struct import unpack
from collections import namedtuple
from sys import stdin
import platform

if platform.system() == "Windows":
    import msvcrt
else:
    import select

def kbhit():
    if platform.system() == "Windows":
        return msvcrt.kbhit()
    else:
        inrdy, _, __ = select.select([sys.stdin], [], [], 0.001)
        return len(inrdy) > 0

CANFrame = namedtuple('CANFrame',
            ['sentinel_start', 'id', 'rtr', 'length', 'data', 'sentinel_end'])


def unpack_packet(data):
    fmt = "<BH?BxxxxxxxxB"
    (sentinel_start, can_id, rtr, length, sentinel_end) = unpack(fmt, data)
    can_data = np.fromstring(data[5:13], dtype=np.uint8)[:length]
    return CANFrame(sentinel_start, can_id, rtr, length, can_data, sentinel_end)


def messages(port, verbose=False):
    PACKET_SIZE = 14
    SYNC_PACKETS = 2
    SENTINEL_VALUE = 0xAA
    def synchronize():
        # Synchronize to the message frames
        consecutive_zeros = 0
        iters = 0
        if verbose:
            print "Resynchronizing..."
        sync_start = time()
        while consecutive_zeros < PACKET_SIZE * SYNC_PACKETS:
            if ord(port.read()[0]) == 0:
                consecutive_zeros += 1
            else:
                consecutive_zeros = 0
            iters += 1
            if verbose and time() - sync_start > 1:
                print "Resynchronizing...(%d)" % iters
                sync_start = time()
        #print "Successfully synchronized!"

    def is_sync_packet(packet):
        return np.all(np.fromstring(packet, dtype=np.uint8) == 0)

    synchronize()
    consecutive_sync_packets = 0
    while True:
        data = port.read(PACKET_SIZE)
        if is_sync_packet(data):
            if verbose and not consecutive_sync_packets:
                print "Discarding sync packet"
            consecutive_sync_packets += 1
            if consecutive_sync_packets == SYNC_PACKETS:
                consecutive_sync_packets = 0
            continue
        else:
            if consecutive_sync_packets:
                # Got a data frame after an incorrect number of
                # sync packets. Better resynchronize.
                synchronize()
                consecutive_sync_packets = 0
                continue
            packet = unpack_packet(data)
            if packet.sentinel_start != SENTINEL_VALUE or \
                packet.sentinel_end != SENTINEL_VALUE:
                # Erroneous packet. We must have desynchronized.
                synchronize()
                continue
            yield packet

def main():
    port = Serial(baudrate=115200)
    try:
        port.setDTR(DTR_CONTROL_DISABLE)
    except ValueError:
        print "Warning: pySerial 2.6 under Windows is too old"
        print "You must use a newer rev to avoid resetting the board"
        print "upon connection"
        print
    port.port = "COM7"
    port.open()
    curses_view(port)

def curses_view(port):
    # Windows version of _curses at:
    # http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses
    import curses
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    height = 25
    win = curses.newwin(height, 80, 0, 0)

    ids_seen = []
    id_to_last_msg = {}
    for msg in messages(port):
        id_to_last_msg[msg.id] = msg
        if msg.id not in ids_seen:
            ids_seen.append(msg.id)
            ids_seen.sort()
            full_redraw = True
        ids_to_draw = []
        if full_redraw:
            ids_to_draw.extend(ids_seen[:height])
        elif ids_seen.index(id) < height:
            ids_to_draw.append(id)

        for id in ids_to_draw:
            row = ids_seen.index(id)
            msg = id_to_last_msg[id]
            text = "%04X\t%s\t%d\t%s" % \
                (msg.id, 'T' if msg.rtr else 'F', msg.length,
                 "  ".join(map(lambda x: '%02X' % x, msg.data)))
            win.addstr(row, 0, text)
        win.refresh()
        if kbhit():
            while kbhit():
                stdin.read(1)
            break

    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()

def dump_messages(port):
    cnt = 0
    for msg in messages(port):
        if msg.id == 0x04B0:
            print "%04X\t%s\t%d\t%s" % \
                (msg.id, 'T' if msg.rtr else 'F', msg.length,
                 "  ".join(map(lambda x: '%02X' % x, msg.data)))
        if kbhit():
            while kbhit():
                stdin.read(1)
            return

if __name__ == "__main__":
    main()
