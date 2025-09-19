from europi import *
from europi_script import EuroPiScript
import utime
import random

class SimpleBitGarden(EuroPiScript):
    def __init__(self):
        # Chromatyczny zestaw nut
        self.root_list = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B", "Cb"]
        # Tryby muzyczne
        self.scale_list = ["Ion", "Dor", "Phryg", "Lyd", "Mixo", "Aeol", "Locr"]

        self.root_idx = 0    # indeks aktualnego root
        self.scale_idx = 0   # indeks aktualnej skali

        self.gate_probs = [0.5, 0.5, 0.5]
        self.gate_lens = [100, 100, 100]
        # Menu: root, scale, G1%, G2%, G3%, G1ms, G2ms, G3ms
        self.menu_items = [
            "Root", "Scale",
            "G1%", "G2%", "G3%",
            "G1ms", "G2ms", "G3ms"
        ]
        self.menu_idx = 0
        self.gate_out = [cv1, cv2, cv3]
        self.gate_state = [False, False, False]
        self.gate_timer = [0, 0, 0]
        self.edit_mode = False    # Tryb edycji parametru
        self.edit_val = None      # Tymczasowa wartość w trakcie edycji
        self.draw_menu(force=True)

    def draw_menu(self, force=False):
        oled.fill(0)
        # ----------- PIERWSZY WIERSZ, y=0 -----------------
        oled.text("scale:", 0, 0)
        oled.text(self.root_list[self.root_idx], 60, 0)
        #oled.text("skl:", 54, 0)
        oled.text(self.scale_list[self.scale_idx], 90, 0)

        # ----------- POZOSTAŁE WIERSZE --------------------
        # Wiersz 1: G1
        y = 9
        g = 0
        marker_p = ">>" if self.edit_mode and self.menu_idx == 2 else (">" if self.menu_idx == 2 else " ")
        prob_txt = f"{marker_p}{int(self.edit_val*100) if self.edit_mode and self.menu_idx==2 else int(self.gate_probs[0]*100)}%"
        marker_l = ">>" if self.edit_mode and self.menu_idx == 5 else (">" if self.menu_idx == 5 else " ")
        len_txt = f"{marker_l}{self.edit_val if self.edit_mode and self.menu_idx==5 else self.gate_lens[0]}ms"
        oled.text("G1:", 0, y)
        oled.text(prob_txt, 28, y)
        oled.text(len_txt, 78, y)

        # Wiersz 2: G2
        y = 17
        g = 1
        marker_p = ">>" if self.edit_mode and self.menu_idx == 3 else (">" if self.menu_idx == 3 else " ")
        prob_txt = f"{marker_p}{int(self.edit_val*100) if self.edit_mode and self.menu_idx==3 else int(self.gate_probs[1]*100)}%"
        marker_l = ">>" if self.edit_mode and self.menu_idx == 6 else (">" if self.menu_idx == 6 else " ")
        len_txt = f"{marker_l}{self.edit_val if self.edit_mode and self.menu_idx==6 else self.gate_lens[1]}ms"
        oled.text("G2:", 0, y)
        oled.text(prob_txt, 28, y)
        oled.text(len_txt, 78, y)

        # Wiersz 3: G3
        y = 25
        g = 2
        marker_p = ">>" if self.edit_mode and self.menu_idx == 4 else (">" if self.menu_idx == 4 else " ")
        prob_txt = f"{marker_p}{int(self.edit_val*100) if self.edit_mode and self.menu_idx==4 else int(self.gate_probs[2]*100)}%"
        marker_l = ">>" if self.edit_mode and self.menu_idx == 7 else (">" if self.menu_idx == 7 else " ")
        len_txt = f"{marker_l}{self.edit_val if self.edit_mode and self.menu_idx==7 else self.gate_lens[2]}ms"
        oled.text("G3:", 0, y)
        oled.text(prob_txt, 28, y)
        oled.text(len_txt, 78, y)

        # ----------- DODATKOWO: root/scale tryb edycji ----------
        if self.menu_idx == 0:
            marker = ">>" if self.edit_mode else ">"
            oled.text(marker, 50, 0)
        elif self.menu_idx == 1:
            marker = ">>" if self.edit_mode else ">"
            oled.text(marker, 80, 0)
        oled.show()

    def update_menu(self):
        if not self.edit_mode:
            # k2: zmiana pozycji menu - 8 pozycji (0..7)
            idx = k2.range(len(self.menu_items))
            if idx != self.menu_idx:
                self.menu_idx = idx
                self.draw_menu(force=True)
        else:
            # Tryb edycji
            k2v = k2.percent()
            if self.menu_idx == 0:
                # Edycja root
                new_idx = int(k2v * (len(self.root_list) - 1) + 0.5)
                if self.edit_val != new_idx:
                    self.edit_val = new_idx
                    self.draw_menu(force=True)
            elif self.menu_idx == 1:
                # Edycja skali
                new_idx = int(k2v * (len(self.scale_list) - 1) + 0.5)
                if self.edit_val != new_idx:
                    self.edit_val = new_idx
                    self.draw_menu(force=True)
            elif 2 <= self.menu_idx <= 4:
                # Edycja prawdopodobieństwa
                new_val = round(k2v, 2)
                if self.edit_val != new_val:
                    self.edit_val = new_val
                    self.draw_menu(force=True)
            elif 5 <= self.menu_idx <= 7:
                # Edycja długości
                new_len = int(10 + k2v * 990)
                if self.edit_val != new_len:
                    self.edit_val = new_len
                    self.draw_menu(force=True)

    def handle_b2(self):
        # Przycisk b2: start/koniec edycji
        if not self.edit_mode:
            # Wejście w tryb edycji - zapamiętaj aktualną wartość
            if self.menu_idx == 0:
                self.edit_val = self.root_idx
            elif self.menu_idx == 1:
                self.edit_val = self.scale_idx
            elif 2 <= self.menu_idx <= 4:
                self.edit_val = self.gate_probs[self.menu_idx - 2]
            elif 5 <= self.menu_idx <= 7:
                self.edit_val = self.gate_lens[self.menu_idx - 5]
            self.edit_mode = True
            self.draw_menu(force=True)
        else:
            # Zapisz edytowaną wartość i wyjdź z trybu edycji
            if self.menu_idx == 0:
                self.root_idx = self.edit_val
            elif self.menu_idx == 1:
                self.scale_idx = self.edit_val
            elif 2 <= self.menu_idx <= 4:
                self.gate_probs[self.menu_idx - 2] = self.edit_val
            elif 5 <= self.menu_idx <= 7:
                self.gate_lens[self.menu_idx - 5] = self.edit_val
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
    
