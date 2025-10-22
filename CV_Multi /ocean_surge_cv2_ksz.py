#!/usr/bin/env python3

from europi import *
from europi_script import EuroPiScript
from experimental.knobs import *
from experimental.screensaver import OledWithScreensaver
import math
import time

# --- Stałe parametry ---
LOW_SWELL = 0.2
HIGH_SWELL = 0.8
LOW_AGITATION = 0.2
HIGH_AGITATION = 0.8
SPREAD = 0.5

MIN_SPEED = 0.01
MAX_SPEED = 1.0
FILTER_WINDOW = 5

MIN_RADIUS = 0.01
MAX_RADIUS = 2
MIN_LENGTH = 1
MAX_LENGTH = 20
MAX_BUOY_SPREAD = 10
two_pi = 2 * math.pi

MAX_OUTPUT_VOLTAGE = 10.0

ssoled = OledWithScreensaver()

def rescale(x, x_min, x_max, y_min, y_max):
    return (x - x_min) / (x_max - x_min) * (y_max - y_min) + y_min

def wave_y(swell, agitation, spread, t):
    r = rescale(agitation, 0.0, 1.0, MIN_RADIUS, MAX_RADIUS)
    wavelength = rescale(swell, 0.0, 1.0, MIN_LENGTH, MAX_LENGTH)
    buoy_x = MAX_BUOY_SPREAD * spread
    return r * math.cos(t - 2 * math.pi * buoy_x / wavelength)

def clip_wave(y):
    return max(-1, min(1, y))

def wave_to_cv(y):
    return ((y + 1) / 2) * MAX_OUTPUT_VOLTAGE

class SimpleOceanSurge(EuroPiScript):
    def __init__(self):
        super().__init__()
        self.k1 = KnobBank.builder(k1).with_unlocked_knob("speed1").build()
        self.k2 = KnobBank.builder(k2).with_unlocked_knob("speed2").build()
        self.speed1_buffer = [self.k1["speed1"].percent()] * FILTER_WINDOW
        self.speed2_buffer = [self.k2["speed2"].percent()] * FILTER_WINDOW
        self.t1 = 0.0
        self.t2 = 0.0
        self.cv1_val = 0.0
        self.cv2_val = 0.0

    def main(self):
        while True:
            # Filtracja potencjometru (moving average) dla obu speed
            self.speed1_buffer.pop(0)
            self.speed1_buffer.append(self.k1["speed1"].percent())
            smoothed1 = sum(self.speed1_buffer) / len(self.speed1_buffer)
            speed1 = smoothed1 * (MAX_SPEED - MIN_SPEED) + MIN_SPEED

            self.speed2_buffer.pop(0)
            self.speed2_buffer.append(self.k2["speed2"].percent())
            smoothed2 = sum(self.speed2_buffer) / len(self.speed2_buffer)
            speed2 = smoothed2 * (MAX_SPEED - MIN_SPEED) + MIN_SPEED

            dt = 0.01

            self.t1 += speed1 * dt
            self.t2 += speed2 * dt
            if self.t1 > two_pi:
                self.t1 -= two_pi
            if self.t2 > two_pi:
                self.t2 -= two_pi

            y1 = clip_wave(wave_y(LOW_SWELL, LOW_AGITATION, SPREAD, self.t1))
            y2 = clip_wave(wave_y(HIGH_SWELL, HIGH_AGITATION, SPREAD, self.t2))
            self.cv1_val = wave_to_cv(y1)
            self.cv2_val = wave_to_cv(y2)

            cv1.voltage(self.cv1_val)
            cv2.voltage(self.cv2_val)

            ssoled.fill(0)
            ssoled.text(f"S1 {speed1:.2f}Hz", 1, 1, 1)
            ssoled.text(f"S2 {speed2:.2f}Hz", 1, CHAR_HEIGHT+2, 1)
            ssoled.text(f"CV1 {self.cv1_val:.2f}V", 1, 2*CHAR_HEIGHT+3, 1)
            ssoled.text(f"CV2 {self.cv2_val:.2f}V", 1, 3*CHAR_HEIGHT+4, 1)
            ssoled.show()

            time.sleep(dt)

if __name__ == "__main__":
    SimpleOceanSurge().main()
