from europi import *
from europi_script import EuroPiScript
import utime
import random

class SimpleBitGarden(EuroPiScript):
    def __init__(self):
        self.gate_probs = [0.5, 0.5, 0.5]
        self.gate_lens = [100, 100, 100]
        self.menu_items = [
            "Gate1 Prob", "Gate2 Prob", "Gate3 Prob",
            "Gate1 Len", "Gate2 Len", "Gate3 Len"
        ]
        self.menu_idx = 0
        self.gate_out = [cv1, cv2, cv3]
        self.gate_state = [False, False, False]
        self.gate_timer = [0, 0, 0]
        self.last_menu_idx = -1
        self.last_val = -1
        self.last_draw = 0
        self.draw_menu(force=True)

    def draw_menu(self, force=False):
        oled.fill(0)
        for i, item in enumerate(self.menu_items):
            marker = ">" if i == self.menu_idx else " "
            if i < 3:
                val = f"{int(self.gate_probs[i]*100)}%"
            else:
                val = f"{self.gate_lens[i-3]}ms"
            oled.text(f"{marker}{item}:{val}", 0, i*10)
        oled.show()

    def update_menu(self):
        # K1: zmiana pozycji menu - 6 pozycji (0..5)
        idx = int(k1.value() * len(self.menu_items))
        idx = min(len(self.menu_items)-1, idx)
        if idx != self.menu_idx:
            self.menu_idx = idx
            self.draw_menu(force=True)

        # K2: ustaw wartość dla aktualnej pozycji menu
        k2v = k2.value()
        if self.menu_idx < 3:
            new_val = round(k2v, 2)  # 0.00–1.00
            if abs(self.gate_probs[self.menu_idx] - new_val) > 0.01:
                self.gate_probs[self.menu_idx] = new_val
                self.draw_menu(force=True)
        else:
            new_len = int(10 + k2v*990)  # 10–1000 ms
            i = self.menu_idx - 3
            if abs(self.gate_lens[i] - new_len) > 3:
                self.gate_lens[i] = new_len
                self.draw_menu(force=True)

    def handle_clock(self):
        for ch in range(3):
            if random.random() < self.gate_probs[ch]:
                self.gate_out[ch].voltage(5)
                self.gate_state[ch] = True
                self.gate_timer[ch] = utime.ticks_add(utime.ticks_ms(), self.gate_lens[ch])
            else:
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def update_gates(self):
        now = utime.ticks_ms()
        for ch in range(3):
            if self.gate_state[ch] and utime.ticks_diff(now, self.gate_timer[ch]) > 0:
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def main(self):
        last_clock = False
        last_menu_update = utime.ticks_ms()
        while True:
            now = utime.ticks_ms()
            # Odświeżenie menu/potencjometrów co 0.1s
            if utime.ticks_diff(now, last_menu_update) > 100:
                self.update_menu()
                last_menu_update = now

            # Obsługa triggera
            clk = digitalin.read() > 0.5
            if clk and not last_clock:
                self.handle_clock()
            last_clock = clk

            self.update_gates()
            utime.sleep_ms(5)

script = SimpleBitGarden()
if __name__ == "__main__":
    script.main()
    

