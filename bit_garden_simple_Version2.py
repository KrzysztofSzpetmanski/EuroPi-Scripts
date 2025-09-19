from europi import *
from europi_script import EuroPiScript
import utime
import random

class SimpleBitGarden(EuroPiScript):
    def __init__(self):
        self.gate_probs = [0.5, 0.5, 0.5]   # Prawdopodobieństwa (0..1)
        self.gate_lens = [100, 100, 100]    # Długości gate w ms
        self.menu_idx = 0
        self.menu_items = [
            "Gate1 Prob",
            "Gate2 Prob",
            "Gate3 Prob",
            "Gate1 Len",
            "Gate2 Len",
            "Gate3 Len"
        ]
        self.edit_mode = False
        self.gate_out = [cv1, cv2, cv3]
        self.gate_state = [False, False, False]
        self.gate_timer = [0, 0, 0]
        self.k1_last = k1.read_position()
        self.k2_last = k2.read_position()
        self.draw_menu()

    def draw_menu(self):
        oled.fill(0)
        for i, item in enumerate(self.menu_items):
            marker = ">" if i == self.menu_idx else " "
            edit = "*" if (self.edit_mode and i == self.menu_idx) else " "
            # Wyświetl wartość
            if i < 3:
                val = f"{int(self.gate_probs[i]*100)}%"
            else:
                val = f"{self.gate_lens[i-3]}ms"
            oled.text(f"{marker}{item}:{val}{edit}", 0, i*10)
        oled.show()

    def handle_menu(self):
        # K1: zmiana menu_idx (poza edycją)
        k1_pos = k1.read_position()
        if not self.edit_mode and k1_pos != self.k1_last:
            diff = k1_pos - self.k1_last
            if diff != 0:
                self.menu_idx = (self.menu_idx + diff) % len(self.menu_items)
                self.draw_menu()
            self.k1_last = k1_pos

        # K2: zmiana wartości (w edycji)
        k2_pos = k2.read_position()
        if self.edit_mode and k2_pos != self.k2_last:
            diff = k2_pos - self.k2_last
            if diff != 0:
                self.change_value(diff)
                self.draw_menu()
            self.k2_last = k2_pos

    def change_value(self, step):
        idx = self.menu_idx
        if idx < 3:
            # Zmiana prawdopodobieństwa
            val = self.gate_probs[idx] + 0.05 * step
            self.gate_probs[idx] = min(1.0, max(0.0, val))
        else:
            # Zmiana długości gate
            i = idx - 3
            val = self.gate_lens[i] + 10 * step
            self.gate_lens[i] = min(1000, max(10, val))

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
        while True:
            # b1: przełącza tryb edycji
            if b1.read():
                self.edit_mode = not self.edit_mode
                self.draw_menu()
                utime.sleep_ms(250)
            self.handle_menu()

            # Obsługa triggera
            clk = digitalin.read() > 0.5
            if clk and not last_clock:
                self.handle_clock()
            last_clock = clk

            self.update_gates()
            utime.sleep_ms(5)

script = SimpleBitGarden()