from arduino import CANFrame
from time import sleep
from time import time
import tables
import numpy as np

class HDF5Frame(tables.IsDescription):
    timestamp = tables.UInt64Col() # Microseconds
    sentinel_start = tables.UInt8Col()
    id = tables.UInt16Col()
    rtr = tables.BoolCol()
    length = tables.UInt8Col()
    data = tables.UInt8Col(shape=(8,))
    sentinel_end = tables.UInt8Col()

_H5_LOG_TABLE = "CANFrames"

class HDF5Source(object):
    def __init__(self, filename, ratelimit=False):
        self.logfile = tables.openFile(filename, 'r')
        self.log = self.logfile.root._f_getChild(_H5_LOG_TABLE)
        self.rate_limit = ratelimit

    def __del__(self):
        self.logfile.close()
    
    def __iter__(self):
        last_returned = float('inf')
        last_timestamp = float('inf')
        for row in self.log.iterrows():
            if self.rate_limit:
                inter_frame_delay = row['timestamp'] - last_timestamp
                cur_time = time()
                if (cur_time - last_returned) * 1e6 < inter_frame_delay:
                    sleep(inter_frame_delay/1e6 - (cur_time - last_returned))
                last_returned = time()
                last_timestamp = row['timestamp']
            # Truncate data if necessary
            kwargs = dict((field, row[field]) for field in
                    ('sentinel_start', 'sentinel_end', 'rtr', 'length', 'id'))
            yield CANFrame(data=row['data'][:row['length']], **kwargs)


class HDF5Sink(object):
    def __init__(self, filename):
        self.logfile = tables.openFile(filename, "w")
        filters = tables.Filters(complevel=9, complib='zlib')
        self.log = self.logfile.createTable(self.logfile.root, _H5_LOG_TABLE,
                HDF5Frame, "CAN Frames from Arduino", filters=filters)
        self.writes_per_flush = 1024
        self.writes_since_flush = 0
        self.start_ts = int(time() * 1e6)
        return

    def __del__(self):
        self.logfile.close()

    def writeFrame(self, frame):
        timestamp = int(time() * 1e6) - self.start_ts
        h5frame = self.log.row
        h5frame['timestamp'] = timestamp
        h5frame['sentinel_start'] = frame.sentinel_start
        h5frame['id'] = frame.id
        h5frame['rtr'] = frame.rtr
        h5frame['length'] = frame.length
        h5frame['sentinel_end'] = frame.sentinel_end

        # Pad data to 8 bytes
        data = np.zeros((8,), dtype=np.uint8)
        data[:frame.length] = frame.data
        h5frame['data'] = data
        
        h5frame.append()
        self.writes_since_flush += 1
        if self.writes_since_flush >= self.writes_per_flush:
            self.writes_since_flush = 0
            self.log.flush()
        return
