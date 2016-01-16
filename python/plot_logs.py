from hdf5_log import HDF5Source
from sys import argv
import pylab
from scipy.signal import fftconvolve
from scipy.interpolate import interp1d
import numpy as np

def to_kph(data):
    return ((data[0] * 256.0 + data[1]) - 10000) / 100

def to_rpm(data):
    return (data[0] * 256.0 + data[1]) / 4

def compute_g(wheelspeed):
    lfdata = wheelspeed[0:2]
    rfdata = wheelspeed[2:4]
    lrdata = wheelspeed[4:6]
    rrdata = wheelspeed[6:8]
    # 5/18 m/s per kph
    vl = 5.0/18 * (to_kph(lfdata) + to_kph(lrdata)) / 2.0
    vr = 5.0/18 * (to_kph(rfdata) + to_kph(rrdata)) / 2.0
    wheel_sep = 1.65 # meters
    return (vl * (vr-vl) / wheel_sep) / 9.8 # 9.8 m/s^2 per g
    
def interpolate(timed_data, method='zero'):
    t, y = zip(*timed_data)
    print "\t",len(t),"frames"
    t = np.array(t)
    y = np.array(y)
    main_interpolator = interp1d(x=t, y=y, kind=method)
    def _interp(x):
        if x < t[0]:
            return y[0]
        elif x > t[-1]:
            return y[-1]
        else:
            return main_interpolator(x)
    return np.vectorize(_interp)


def main():
    # Divide by 1e3 to convert ms -> sec
    frames = [(frame.sender_timestamp / 1e3, frame) for frame in
                HDF5Source(argv[1])]
    frames.sort(key=lambda x:x[0])
    frames = frames[:-1] # Hack, for data files with bad last frame
    print "Loaded frames"
    start_time = min(ts for ts, frame in frames)
    end_time = max(ts for ts, frame in frames)
    frames = [(ts - start_time, frame) for ts, frame in frames]
    print "Renormalized times"

    speed = interpolate([(ts, to_kph(frame.data[4:6]))
                for ts, frame in frames if frame.id == 0x0201])
    print "Constructed speed interpolator"

    rpm = interpolate([(ts, to_rpm(frame.data))
                for ts, frame in frames if frame.id == 0x0201])
    print "Constructed rpm interpolator"

    #throttle = interpolate([(ts, frame.data[6] / 2.0)
    #            for ts, frame in frames if frame.id == 0x0201])
    #brake = interpolate([(ts, (frame.data[5] & 0x08) >> 3)
    #            for ts, frame in frames if frame.id == 0x0212])
    lateral_g = interpolate([(ts, compute_g(frame.data))
                for ts, frame in frames if frame.id == 0x04B0])
    print "Constructed g interpolator"
    debug_frames = [(ts, frame) for ts, frame in frames if
                    frame.id == 0xFFFF]
    print "Extracted debug frames"

    drive_time_sec = (end_time - start_time)
    print start_time
    print end_time
    print drive_time_sec
    print min(ts for ts, frame in frames if frame.id == 0x0201)
    print max(ts for ts, frame in frames if frame.id == 0x0201)
    print min(ts for ts, frame in frames if frame.id == 0x04B0)
    print max(ts for ts, frame in frames if frame.id == 0x04B0)
    # Plot at 10Hz from first sec to second to last sec (bounds)
    sampling_rate = 10.0
    time = np.arange(0, drive_time_sec, 1.0/sampling_rate)
    print time.shape
    print min(time)
    print max(time)
    speeds = speed(time)
    print "Computed speed"
    rpms = rpm(time)
    print "Computed rpm"
    gs = lateral_g(time)
    print "Computed g"
    debug_times = [ts for ts, frames in debug_frames]
    
    fig = pylab.figure()
    s1a1 = fig.add_subplot(2,1,1)
    pylab.hold(True)
    s1a1.stem(debug_times, [150 for x in debug_times], 'k')
    s1a1.plot(time, speeds, 'b')
    s1a1.set_ylabel('Speed (kph)')
    s1a1.set_xlabel('Time (s)')
    s1a2 = s1a1.twinx()
    s1a2.plot(time, rpms, 'r')
    s1a2.set_ylabel('RPM')
    s2a1 = fig.add_subplot(2,1,2)
    s2a1.plot(time, gs)
    s2a1.set_ylabel('Lateral g (+ indicates left turn)')
    s2a1.set_xlabel('Time (s)')
    pylab.show()

if __name__ == "__main__":
    main()
