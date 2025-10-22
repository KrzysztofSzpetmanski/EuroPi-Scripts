#!/usr/bin/env python3

from europi import *
from europi_script import EuroPiScript
from experimental.knobs import *
from experimental.screensaver import OledWithScreensaver
import random
import time

MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 10.0
MIN_FREQUENCY = 0.01
MAX_FREQUENCY = 10.0
FILTER_WINDOW = 5  # liczba próbek do uśredniania

ssoled = OledWithScreensaver()

class RandomStepCV(EuroPiScript):
    def __init__(self):
        super().__init__()
        self.freq_knob = KnobBank.builder(k1).with_unlocked_knob("freq").build()
        # Bufor do uśredniania wartości potencjometru
        start_val = self.freq_knob["freq"].percent()
        self.freq_buffer = [start_val] * FILTER_WINDOW
        self.last_tick = time.ticks_ms()
        self.current_voltage = 0.0
        self.freq = MIN_FREQUENCY  # inicjacja

    def main(self):
        while True:
            # Uśrednianie odczytu potencjometru (moving average)
            self.freq_buffer.pop(0)
            self.freq_buffer.append(self.freq_knob["freq"].percent())
            smoothed_percent = sum(self.freq_buffer) / len(self.freq_buffer)
            self.freq = smoothed_percent * (MAX_FREQUENCY - MIN_FREQUENCY) + MIN_FREQUENCY
            period_ms = 1000.0 / self.freq

            now = time.ticks_ms()
            elapsed = time.ticks_diff(now, self.last_tick)

            if elapsed >= period_ms:
                self.current_voltage = random.uniform(MIN_VOLTAGE, MAX_VOLTAGE)
                cv1.voltage(self.current_voltage)
                self.last_tick = now

            # OLED: tylko freq i napięcie
            ssoled.fill(0)
            ssoled.text(f"F {self.freq:.2f}Hz", 1, 1, 1)
            ssoled.text(f"V {self.current_voltage:.2f}V", 1, CHAR_HEIGHT+2, 1)
            ssoled.show()

if __name__ == "__main__":
    RandomStepCV().main()
