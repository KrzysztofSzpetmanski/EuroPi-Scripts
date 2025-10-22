#!/usr/bin/env python3

from europi import *
from europi_script import EuroPiScript

from experimental.knobs import *
from experimental.math_extras import solve_linear_system
from experimental.screensaver import OledWithScreensaver

import configuration
import math
import random
import time

ssoled = OledWithScreensaver()

CLIP_MODE_LIMIT = 0
CLIP_MODE_FOLD = 1
CLIP_MODE_THRU = 2
CLIP_MODE_NAMES = [
    "Limit",
    "Fold",
    "Thru"
]

AIN_MODE_FREQUENCY = "frequency"
AIN_MODE_CURVE = "curve"

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

class OutputChannel:
    def __init__(self, script, frequency_in, curve_in, cv_out):
        self.script = script
        self.curve = BezierCurve()
        self.cv_out = cv_out
        self.frequency_in = frequency_in
        self.curve_in = curve_in
        self.voltage_out = 0
        self.cv_out.off()
        self.last_tick_at = time.ticks_ms()
        self.change_voltage()
        self.frequency = 0.0
        self.curve_k = 0.0
        self.voltage_out = 0.0
        self.vizualization_samples = []

    def change_voltage(self):
        self.curve.set_next_value(random.random() * 1.2 - 0.1)

    def update(self, clip_mode=CLIP_MODE_LIMIT):
        now = time.ticks_ms()
        self.curve_k = self.curve_in.percent() * 2 - 1
        self.frequency = self.frequency_in.percent() * (self.script.config.MAX_FREQUENCY - self.script.config.MIN_FREQUENCY) + self.script.config.MIN_FREQUENCY
        t = 1000.0/self.frequency
        elapsed_ms = time.ticks_diff(now, self.last_tick_at)
        if elapsed_ms >= t:
            self.change_voltage()
            self.last_tick_at = now
            elapsed_ms = 0
        self.voltage_out = self.curve.value_at(elapsed_ms / t, self.curve_k) * (self.script.config.MAX_VOLTAGE - self.script.config.MIN_VOLTAGE) + self.script.config.MIN_VOLTAGE

        if clip_mode == CLIP_MODE_LIMIT:
            self.voltage_out = self.clip_limit(self.voltage_out)
        elif clip_mode == CLIP_MODE_FOLD:
            self.voltage_out = self.clip_fold(self.voltage_out)
        elif clip_mode == CLIP_MODE_THRU:
            self.voltage_out = self.clip_thru(self.voltage_out)

        self.cv_out.voltage(self.voltage_out)
        self.vizualization_samples.append(int((self.voltage_out - self.script.config.MIN_VOLTAGE) / (self.script.config.MAX_VOLTAGE - self.script.config.MIN_VOLTAGE) * OLED_HEIGHT/3))
        if len(self.vizualization_samples) > OLED_WIDTH:
            self.vizualization_samples.pop(0)

    def clip_limit(self, v):
        if v < self.script.config.MIN_VOLTAGE:
            return self.script.config.MIN_VOLTAGE
        elif v > self.script.config.MAX_VOLTAGE:
            return self.script.config.MAX_VOLTAGE
        else:
            return v

    def clip_fold(self, v):
        if v < self.script.config.MIN_VOLTAGE:
            return self.script.config.MIN_VOLTAGE - v
        elif v > self.script.config.MAX_VOLTAGE:
            return self.script.config.MAX_VOLTAGE + (self.script.config.MAX_VOLTAGE - v)
        else:
            return v

    def clip_thru(self, v):
        if v < self.script.config.MIN_VOLTAGE:
            return self.script.config.MAX_VOLTAGE - (self.script.config.MIN_VOLTAGE - v)
        elif v > self.script.config.MAX_VOLTAGE:
            return self.script.config.MIN_VOLTAGE - (self.script.config.MAX_VOLTAGE - v)
        else:
            return v

class BezierSingle(EuroPiScript):
    def __init__(self):
        super().__init__()
        cfg = self.load_state_json()
        self.frequency_in = KnobBank.builder(k1).with_unlocked_knob("main").build()
        self.curve_in = KnobBank.builder(k2).with_unlocked_knob("main").build()
        self.clip_mode = cfg.get("clip_mode", CLIP_MODE_LIMIT)
        self.settings_dirty = False
        self.curve = OutputChannel(self, self.frequency_in["main"], self.curve_in["main"], cv1)

        @b1.handler
        def on_b1_press():
            self.clip_mode = (self.clip_mode + 1) % len(CLIP_MODE_NAMES)
            self.settings_dirty = True
            ssoled.notify_user_interaction()

    @classmethod
    def config_points(cls):
        import europi_config
        def restrict_input_voltage(v):
            if v > europi_config.MAX_INPUT_VOLTAGE:
                return europi_config.MAX_INPUT_VOLTAGE
            return v
        return [
            configuration.floatingPoint(
                name="MAX_INPUT_VOLTAGE",
                minimum=0.0,
                maximum=europi_config.MAX_INPUT_VOLTAGE,
                default=restrict_input_voltage(10.0)
            ),
            configuration.floatingPoint(
                name="MIN_VOLTAGE",
                minimum=0.0,
                maximum=europi_config.MAX_OUTPUT_VOLTAGE,
                default=0.0
            ),
            configuration.floatingPoint(
                name="MAX_VOLTAGE",
                minimum=0.0,
                maximum=europi_config.MAX_OUTPUT_VOLTAGE,
                default=europi_config.MAX_OUTPUT_VOLTAGE
            ),
            configuration.floatingPoint(
                name="MIN_FREQUENCY",
                minimum=0.001,
                maximum=10.0,
                default=0.01
            ),
            configuration.floatingPoint(
                name="MAX_FREQUENCY",
                minimum=0.001,
                maximum=10.0,
                default=1.0
            )
        ]

    def save(self):
        cfg = {
            "clip_mode": self.clip_mode
        }
        self.save_state_json(cfg)
        self.settings_dirty = False

    def draw_graph(self, curve):
        for i in range(len(curve.vizualization_samples)):
            ssoled.pixel(i, OLED_HEIGHT - 1 - curve.vizualization_samples[i], 1)

    def main(self):
        UI_DEADZONE = 0.01
        prev_freq_value = self.frequency_in["main"].percent()
        prev_curve_value = self.curve_in["main"].percent()

        while True:
            self.curve.update(self.clip_mode)
            if self.settings_dirty:
                self.save()
            current_freq_value = self.frequency_in["main"].percent()
            current_curve_value = self.curve_in["main"].percent()
            if abs(current_freq_value - prev_freq_value) >= UI_DEADZONE or abs(current_curve_value - prev_curve_value) >= UI_DEADZONE:
                ssoled.notify_user_interaction()
            prev_freq_value = current_freq_value
            prev_curve_value = current_curve_value

            ssoled.fill(0)
            ssoled.text(f"F {self.curve.frequency:0.2f}Hz  K {self.curve.curve_k:+0.2f}", 1, 1, 1)
            ssoled.text(CLIP_MODE_NAMES[self.clip_mode], 1, CHAR_HEIGHT+2, 1)
            self.draw_graph(self.curve)
            ssoled.show()

if __name__ == "__main__":
    BezierSingle().main()