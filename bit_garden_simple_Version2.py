from europi import *
from europi_script import EuroPiScript
import utime
import random

class SimpleBitGarden(EuroPiScript):
    def __init__(self):
        self.gate_probs = [0.5, 0.5, 0.5]
        self.gate_lens = [100, 100, 100]
        self.menu_items = [
            "G1%", "G2%", "G3%",
            "G1ms", "G2ms", "G3ms"
        ]
        self.menu_idx = 0
        self.gate_out = [cv1, cv2, cv3]
        self.gate_state = [False, False, False]
        self.gate_timer = [0, 0, 0]
        self.edit_mode = False    # Dodane: tryb edycji
        self.edit_val = None      # Dodane: wartość tymczasowa podczas edycji
        self.draw_menu(force=True)

    def draw_menu(self, force=False):
        oled.fill(0)
        menu_names = [
            "G1 %", "G2 %", "G3 %",
            "G1 ms", "G2 ms", "G3 ms"
        ]
        mode_str = "EDIT" if self.edit_mode else "NAV"
        oled.text(f"{mode_str}: {menu_names[self.menu_idx]}", 0, 0)
        for i in range(3):
            y = 8 + i * 8
            oled.text(f"G{i+1}:", 0, y)
            # Podświetlanie edytowanego lub wybranego parametru
            if self.menu_idx == i:
                marker = ">>" if self.edit_mode else ">"
            else:
                marker = " "
            # Prawdopodobieństwo
            if self.edit_mode and self.menu_idx == i:
                val_txt = f"{marker}{int(self.edit_val*100)}%"
            else:
                val_txt = f"{marker}{int(self.gate_probs[i]*100)}%"
            oled.text(val_txt, 28, y)
            # Długość
            if self.menu_idx == i+3:
                marker = ">>" if self.edit_mode else ">"
            else:
                marker = " "
            if self.edit_mode and self.menu_idx == i+3:
                len_txt = f"{marker}{self.edit_val}ms"
            else:
                len_txt = f"{marker}{self.gate_lens[i]}ms"
            oled.text(len_txt, 78, y)
        oled.show()

    def update_menu(self):
        if not self.edit_mode:
            # k2: zmiana pozycji menu - 6 pozycji (0..5)
            idx = k2.range(len(self.menu_items))
            if idx != self.menu_idx:
                self.menu_idx = idx
                self.draw_menu(force=True)
        else:
            # W trybie edycji K2 zmienia TYLKO wybrany parametr (reszta się nie rusza)
            k2v = k2.percent()
            if self.menu_idx < 3:
                # Edycja prawdopodobieństwa
                new_val = round(k2v, 2)
                if self.edit_val != new_val:
                    self.edit_val = new_val
                    self.draw_menu(force=True)
            else:
                # Edycja długości
                new_len = int(10 + k2v * 990)
                if self.edit_val != new_len:
                    self.edit_val = new_len
                    self.draw_menu(force=True)

    def handle_b2(self):
        # Przycisk b2: start/koniec edycji
        if not self.edit_mode:
            # Wejście w tryb edycji - zapamiętaj aktualną wartość
            if self.menu_idx < 3:
                self.edit_val = self.gate_probs[self.menu_idx]
            else:
                self.edit_val = self.gate_lens[self.menu_idx-3]
            self.edit_mode = True
            self.draw_menu(force=True)
        else:
            # Zapisz edytowaną wartość i wyjdź z trybu edycji
            if self.menu_idx < 3:
                self.gate_probs[self.menu_idx] = self.edit_val
            else:
                self.gate_lens[self.menu_idx-3] = self.edit_val
            self.edit_mode = False
            self.edit_val = None
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
        last_b2 = b2.value()
        while True:
            now = utime.ticks_ms()
            # Odświeżenie menu/potencjometrów co 0.1s
            if utime.ticks_diff(now, last_menu_update) > 100:
                self.update_menu()
                last_menu_update = now

            # Obsługa triggera
            clk = bool(din.value)
            if clk and not last_clock:
                self.handle_clock()
            last_clock = clk

            # Obsługa przycisku b2
            curr_b2 = b2.value()
            if curr_b2 and not last_b2:
                self.handle_b2()
            last_b2 = curr_b2

            self.update_gates()
            utime.sleep_ms(5)

script = SimpleBitGarden()
if __name__ == "__main__":
    script.main()

