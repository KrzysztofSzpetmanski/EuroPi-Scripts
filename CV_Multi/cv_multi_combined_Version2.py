#!/usr/bin/env python3

from europi import *
from europi_script import EuroPiScript

from experimental.knobs import *
from experimental.math_extras import solve_linear_system
from experimental.screensaver import OledWithScreensaver

import random
import math
import time

# --- Stałe zakresów, filtracji i parametrów ---
MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 10.0
MIN_FREQUENCY = 0.01
MAX_FREQUENCY = 10.0
FILTER_WINDOW = 5
OLED_UPDATE_INTERVAL = 0.1  # sekundy

ssoled = OledWithScreensaver()

# -------- Random Step CV --------
class RandomStepCV:
    def __init__(self, freq_knob, cv_out):
        self.knob = freq_knob
        self.cv_out = cv_out
        start_val = self.knob.percent()
        self.freq_buffer = [start_val] * FILTER_WINDOW
        self.last_tick = time.ticks_ms()
        self.current_voltage = 0.0
        self.freq = MIN_FREQUENCY

    def update(self):
        # Uśrednianie potencjometru
        self.freq_buffer.pop(0)
        self.freq_buffer.append(self.knob.percent())
        smoothed_percent = sum(self.freq_buffer) / len(self.freq_buffer)
        self.freq = smoothed_percent * (MAX_FREQUENCY - MIN_FREQUENCY) + MIN_FREQUENCY
        period_ms = 1000.0 / self.freq

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.last_tick)
        if elapsed >= period_ms:
            self.current_voltage = random.uniform(MIN_VOLTAGE, MAX_VOLTAGE)
            self.cv_out.voltage(self.current_voltage)
            self.last_tick = now

# -------- Bezier Single CV --------
class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def linear_interpolate(x1, x2, t):
    return x1 * (1-t) + x2 * t

class BezierCurve:
    def __init__(self):
        self.origin = Point2D(0, 0)
        self.next_point = Point2D(1, 0)

    def set_next_value(self, y):
        self.origin.y = self.next_point.y
        self.next_point.y = y

    def value_at(self, t, k):
        p1 = self.interpolate(0, k)
        p2 = self.interpolate(1/3, k)
        p3 = self.interpolate(2/3, k)
        p4 = self.interpolate(1, k)
        m = [
            [p1.x**3, p1.x**2, p1.x, 1, p1.y],
            [p2.x**3, p2.x**2, p2.x, 1, p2.y],
            [p3.x**3, p3.x**2, p3.x, 1, p3.y],
            [p4.x**3, p4.x**2, p4.x, 1, p4.y],
        ]
        coeffs = solve_linear_system(m)
        return coeffs[0] * t**3 + coeffs[1] * t**2 + coeffs[2] * t + coeffs[3]

    def interpolate(self, t, k):
        p0 = self.origin
        p1 = Point2D(0,0)
        p2 = Point2D(0,0)
        p3 = self.next_point
        if k <= 0:
            p1.x = p0.x - k/3
            p2.x = p3.x + k/3
            p1.y = p0.y
            p2.y = p3.y
        else:
            p1.x = p0.x
            p2.x = p3.x
            dy = abs(p0.y - p3.y)
            if p0.y < p3.y:
                p1.y = p1.y + dy * k/2
                p2.y = p3.y - dy * k/2
            else:
                p1.y = p1.y - dy * k/2
                p2.y = p3.y + dy * k/2
        q0 = Point2D(
            linear_interpolate(p0.x, p1.x, t),
            linear_interpolate(p0.y, p1.y, t)
        )
        q1 = Point2D(
            linear_interpolate(p1.x, p2.x, t),
            linear_interpolate(p1.y, p2.y, t)
        )
        q2 = Point2D(
            linear_interpolate(p2.x, p3.x, t),
            linear_interpolate(p2.y, p3.y, t)
        )
        r0 = Point2D(
            linear_interpolate(q0.x, q1.x, t),
            linear_interpolate(q0.y, q1.y, t)
        )
        r1 = Point2D(
            linear_interpolate(q1.x, q2.x, t),
            linear_interpolate(q1.y, q2.y, t)
        )
        b = Point2D(
            linear_interpolate(r0.x, r1.x, t),
            linear_interpolate(r0.y, r1.y, t)
        )
        return b

class BezierSingleCV:
    def __init__(self, freq_knob, cv_out, k_fixed):
        self.knob = freq_knob
        self.cv_out = cv_out
        self.k_fixed = k_fixed
        self.freq_buffer = [self.knob.percent()] * FILTER_WINDOW
        self.curve = BezierCurve()
        self.last_tick = time.ticks_ms()
        self.frequency = MIN_FREQUENCY
        self.voltage_out = 0.0
        self.curve.set_next_value(random.uniform(0,1))

    def update(self):
        # Filtrowanie
        self.freq_buffer.pop(0)
        self.freq_buffer.append(self.knob.percent())
        smoothed_percent = sum(self.freq_buffer) / len(self.freq_buffer)
        self.frequency = smoothed_percent * (MAX_FREQUENCY - MIN_FREQUENCY) + MIN_FREQUENCY
        t_duration = 1000.0 / self.frequency
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.last_tick)
        if elapsed >= t_duration:
            self.curve.set_next_value(random.uniform(0,1))
            self.last_tick = now
            elapsed = 0
        v = self.curve.value_at(elapsed / t_duration, self.k_fixed)
        self.voltage_out = v * (MAX_VOLTAGE - MIN_VOLTAGE) + MIN_VOLTAGE
        self.cv_out.voltage(self.voltage_out)

# -------- Ocean Surge uproszczony (CV3/CV6) --------
MIN_RADIUS = 0.01
MAX_RADIUS = 2
MIN_LENGTH = 1
MAX_LENGTH = 20
MAX_BUOY_SPREAD = 10
LOW_SWELL = 0.2
HIGH_SWELL = 0.8
LOW_AGITATION = 0.2
HIGH_AGITATION = 0.8
SPREAD = 0.5
two_pi = 2 * math.pi

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
    return ((y + 1) / 2) * MAX_VOLTAGE

class OceanSurgeSimple:
    def __init__(self, freq_knob, cv_out, swell, agitation, spread=SPREAD):
        self.knob = freq_knob
        self.cv_out = cv_out
        self.swell = swell
        self.agitation = agitation
        self.spread = spread
        self.freq_buffer = [self.knob.percent()] * FILTER_WINDOW
        self.t = 0.0
        self.voltage = 0.0

    def update(self):
        self.freq_buffer.pop(0)
        self.freq_buffer.append(self.knob.percent())
        smoothed_percent = sum(self.freq_buffer) / len(self.freq_buffer)
        speed = smoothed_percent * (MAX_FREQUENCY - MIN_FREQUENCY) + MIN_FREQUENCY
        dt = 0.01
        self.t += speed * dt
        if self.t > two_pi:
            self.t -= two_pi
        y = clip_wave(wave_y(self.swell, self.agitation, self.spread, self.t))
        self.voltage = wave_to_cv(y)
        self.cv_out.voltage(self.voltage)

# -------- Główna klasa --------
class CVMultiCombo(EuroPiScript):
    def __init__(self):
        super().__init__()
        # Knoby
        self.k1 = KnobBank.builder(k1).with_unlocked_knob("freq1").build()
        self.k2 = KnobBank.builder(k2).with_unlocked_knob("freq2").build()

        # CV1, CV4: Random Step
        self.rand_cv1 = RandomStepCV(self.k1["freq1"], cv1)
        self.rand_cv4 = RandomStepCV(self.k2["freq2"], cv4)

        # CV2, CV5: Bezier
        self.bezier_cv2 = BezierSingleCV(self.k1["freq1"], cv2, k_fixed=-1)
        self.bezier_cv5 = BezierSingleCV(self.k2["freq2"], cv5, k_fixed=+1)

        # CV3, CV6: Ocean Surge (przykład: low/high parametry, spread wspólny)
        self.os_cv3 = OceanSurgeSimple(self.k1["freq1"], cv3, LOW_SWELL, LOW_AGITATION, SPREAD)
        self.os_cv6 = OceanSurgeSimple(self.k2["freq2"], cv6, HIGH_SWELL, HIGH_AGITATION, SPREAD)

        self.last_oled_update = time.ticks_ms()
        self.freq1 = MIN_FREQUENCY
        self.freq2 = MIN_FREQUENCY

    def main(self):
        while True:
            # Update wszystkich kanałów
            self.rand_cv1.update()
            self.rand_cv4.update()
            self.bezier_cv2.update()
            self.bezier_cv5.update()
            self.os_cv3.update()
            self.os_cv6.update()

            # Zapisz freq do wyświetlenia
            self.freq1 = self.rand_cv1.freq
            self.freq2 = self.rand_cv4.freq

            # OLED update co OLED_UPDATE_INTERVAL
            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_oled_update) > OLED_UPDATE_INTERVAL * 1000:
                ssoled.fill(0)
                ssoled.text(f"Freq1 {self.freq1:.2f}Hz", 1, 1, 1)
                ssoled.text(f"Freq2 {self.freq2:.2f}Hz", 1, CHAR_HEIGHT+2, 1)
                ssoled.show()
                self.last_oled_update = now

            time.sleep(0.005)

if __name__ == "__main__":
    CVMultiCombo().main()