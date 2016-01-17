def bigendian(data, indices):
    num = 0
    for index in indices:
        num = (num << 8) | data[index]
    return num


class RX8State(object):
    def __init__(self):
        self.brake = False
        self.handbrake = False
        self.dsc = True
        self.rpm = 0
        self.throttle_pct = 0
        self.steering_angle_pct = 0
        self.vehicle_speed_kph = 0
        self.wheelspeed_lf_kph = 0
        self.wheelspeed_rf_kph = 0
        self.wheelspeed_lr_kph = 0
        self.wheelspeed_rr_kph = 0

    def to_string(self):
        def onoff(b):
            return 'ON' if b else 'OFF'

        #line1 = ('RPM % 4.1f THROTTLE % 3.1f%% STEERING % 4.1f%% ' % (
        #            self.rpm, self.throttle_pct, self.steering_angle_pct))
        # Note: there seems to be a bug either in identification of
        # throttle/steering info or in the stored logs. Don't write it
        # to screen for now.
        line1 = 'RPM % 4.1f                                      ' % (
                    self.rpm)
        line1 += 'BRAKE % 3s HANDBRAKE % 3s DSC % 3s' % (
                    onoff(self.brake), onoff(self.handbrake),
                    onoff(self.dsc))
        line2 =\
            'VEHICLE SPEED kph % 3.1f     WHEELS kph: LF % 3.1f RF % 3.1f' % (
                self.vehicle_speed_kph, self.wheelspeed_lf_kph,
                self.wheelspeed_rf_kph)
        line3 =\
            '                                        LR % 3.1f RR % 3.1f' % (
                self.wheelspeed_lr_kph, self.wheelspeed_rr_kph)
        return line1, line2, line3

    @staticmethod
    def speed_to_kph(speed):
        return (speed - 10000) / 100.

    def update(self, frame):
        if frame.id == 0x0081:
            # Steering data: bytes 2-3 big endian. Steering angle
            # between 0xFDE1 and 0x021E.
            angle = bigendian(frame.data, [2,3])
            if angle & 0x8000:
                # Negative angle
                angle = angle - 0xFFFF - 1
            angle /= 543.
            self.steering_angle_pct = angle / 543. * 100
            return True
        elif frame.id == 0x0201:
            self.rpm = bigendian(frame.data, [0, 1]) / 4.
            self.vehicle_speed_kph =\
                self.speed_to_kph(bigendian(frame.data, [4,5]))
            self.throttle_pct = frame.data[6] / 2.
            return True
        elif frame.id == 0x0212:
            self.handbrake = (frame.data[4] & 0x40 != 0)
            self.brake = (frame.data[5] & 0x8 != 0)
            self.dsc = (frame.data[5] & 0x40 != 0)
            return True
        elif frame.id == 0x04B0:
            self.wheelspeed_lf_kph =\
                self.speed_to_kph(bigendian(frame.data, [0,1]))
            self.wheelspeed_rf_kph =\
                self.speed_to_kph(bigendian(frame.data, [2,3]))
            self.wheelspeed_lr_kph =\
                self.speed_to_kph(bigendian(frame.data, [4,5]))
            self.wheelspeed_rr_kph =\
                self.speed_to_kph(bigendian(frame.data, [6,7]))
            return True
        else:
            return False
