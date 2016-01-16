from hdf5_log import HDF5Source
from sys import argv
import numpy as np

def main(logfile):
    id2frames = {}
    frames = [(rts, frame) for rts, frame in
              HDF5Source(logfile, timestamps=True)]
    frames.sort(key=lambda (rts, frame): (rts, frame.sequence))
    timestamps = np.array([(rts, frame.sender_timestamp) for
                            rts, frame in frames])
    h5 = tables.openFile(argv[2], 'w')
    h5.createArray(h5.root, 'timestamps', timestamps)
    h5.close()
    return
    diffs = np.diff(timestamps, axis=0)


    for rts, frame in frames:
        if frame.id not in id2frames:
            id2frames[frame.id] = []
        sts = frame.sender_timestamp
        # Normalize timestamps to seconds
        id2frames[frame.id].append((sts / 1e3, rts / 1e6, frame))
        print "%08x" % sts, "%.3f" % (rts/1000), frame
    print
    print
    for id, frames in id2frames.iteritems():
        print "ID", hex(id)
        last_st, last_rt = frames[0][:2]
        for i, (sts, rts, frame) in enumerate(frames[1:]):
            if sts - last_st > 1:
                print "%08x" % last_st, "%d" % (last_rt/1000), frames[i][2]
                print "%08x" % sts, "%d" % (rts/1000), frame
                print
            last_st = sts
            last_rt = rts
        print
            

if __name__ == "__main__":
    main(argv[1])
