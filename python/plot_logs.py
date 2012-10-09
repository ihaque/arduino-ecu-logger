from hdf5_log import HDF5Source
from sys import argv
import pylab
from scipy.signal import fftconvolve
import numpy as np

def bytes_to_kph(data):
    return ((data[0] * 256.0 + data[1]) - 10000) / 100

def compute_g(wheelspeed):
    lfdata = wheelspeed[0:2]
    rfdata = wheelspeed[2:4]
    lrdata = wheelspeed[4:6]
    rrdata = wheelspeed[6:8]
    # 5/18 m/s per kph
    vl = 5.0/18 * (bytes_to_kph(lfdata) + bytes_to_kph(lrdata)) / 2.0
    vr = 5.0/18 * (bytes_to_kph(rfdata) + bytes_to_kph(rrdata)) / 2.0
    wheel_sep = 1.65 # meters
    return (vl * (vr-vl) / wheel_sep) / 9.8 # 9.8 m/s^2 per g
    

def main():
    speed = []
    throttle = []
    rpm = []
    brake = []
    wheelspeed_data = []
    curspeed, curthrottle, currpm, curbrake, curws = None, None, None, None, None
    for ii, frame in enumerate(HDF5Source(argv[1])):
        update = True
        if frame.id == 0x0212:
            curbrake = frame.data[5] & 0x08
        elif frame.id == 0x0201:
            currpm = (frame.data[0] * 256.0 + frame.data[1]) / 4
            curthrottle = frame.data[6] / 2.0
            curspeed = bytes_to_kph(frame.data[4:6])
        elif frame.id == 0x04B0:
            curws = frame.data
        else:
            update = False

        if curspeed is not None and currpm is not None and \
            curthrottle is not None and curbrake is not None and \
            update:
            speed.append(curspeed)
            throttle.append(curthrottle)
            rpm.append(currpm)
            brake.append(curbrake)
            wheelspeed_data.append(curws)
            if len(rpm) % 10000 == 0:
                print "\tDatum", len(rpm)
    """
    pylab.figure()
    pylab.subplot(5,1,1)
    pylab.plot(throttle)
    pylab.subplot(5,1,2)
    pylab.plot(speed)
    pylab.subplot(5,1,3)
    pylab.plot(rpm)
    pylab.subplot(5,1,4)
    pylab.plot(brake)
    pylab.subplot(5,1,5)
    pylab.plot(map(compute_g, wheelspeed_data))
    """

    pylab.figure()
    pylab.subplot(2,1,1)
    pylab.hold(True)
    pylab.plot(speed, 'k', label='VSS')
    pylab.plot([bytes_to_kph(datum[0:2]) for datum in wheelspeed_data],
                'r', label='LF')
    pylab.plot([bytes_to_kph(datum[2:4]) for datum in wheelspeed_data],
                'b', label='RF')
    pylab.plot([bytes_to_kph(datum[4:6]) for datum in wheelspeed_data],
                'g', label='LR')
    pylab.plot([bytes_to_kph(datum[6:8]) for datum in wheelspeed_data],
                'm', label='RR')
    pylab.legend()
    pylab.subplot(2,1,2)
    g_forces = np.array(map(compute_g, wheelspeed_data))
    pylab.plot(fftconvolve(g_forces, np.array([1.0/30] * 30), mode='same'))
    pylab.show()



if __name__ == "__main__":
    main()
