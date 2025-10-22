from europi import *
from europi_script import EuroPiScript
import utime
import random

class SimpleBitGarden(EuroPiScript):
    def __init__(self):
        self.root_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.octave_min = 0
        self.octave_max = 7
        self.range_min = 1
        self.range_max = 8
        self.scale_list = ["Ion", "Dor", "Phryg", "Lyd", "Mixo", "Aeol", "Locr"]

        self.root_note_idx = 0
        self.root_octave = 0
        self.range_val = 8
        self.scale_idx = 0

        self.gate_probs = [0.5, 0.5, 0.5]
        self.gate_lens = [100, 100, 100]
        self.menu_items = [
            "Root", "Range", "Scale",
            "G1%", "G2%", "G3%",
            "G1ms", "G2ms", "G3ms"
        ]
        self.menu_idx = 0
        self.gate_out = [cv1, cv2, cv3]
        self.gate_state = [False, False, False]
        self.gate_timer = [0, 0, 0]
        self.edit_mode = False
        self.edit_val = None
        self.draw_menu(force=True)

    def get_root_display(self, editing=False):
        if editing and self.menu_idx == 0 and self.edit_val is not None:
            note_idx, octave = self.edit_val
        else:
            note_idx = self.root_note_idx
            octave = self.root_octave
        return f"{self.root_notes[note_idx]}{octave}"

    def get_range_value(self, editing=False):
        if editing and self.menu_idx == 1:
            return self.edit_val
        else:
            return self.range_val

    def draw_menu(self, force=False):
        oled.fill(0)
        # ---- PIERWSZY WIERSZ ----
        oled.text("scl:", 0, 0)

        # Root
        root_x = 36
        marker_root_x = 30
        if self.menu_idx == 0:
            offset = 7 if self.edit_mode else 0
            marker = ">>" if self.edit_mode else ">"
            oled.text(marker, marker_root_x + offset, 0)
            oled.text(self.get_root_display(True), root_x + offset, 0)
        else:
            oled.text(self.get_root_display(False), root_x, 0)

        # Range
        range_x = 80
        marker_range_x = 70
        if self.menu_idx == 1:
            offset = 5 if self.edit_mode else 0
            marker = ">>" if self.edit_mode else ">"
            oled.text(marker, marker_range_x + offset, 0)
            oled.text(str(self.get_range_value(True)), range_x + offset, 0)
        else:
            oled.text(str(self.get_range_value(False)), range_x, 0)

        # Scale
        scale_x = 95
        marker_scale_x = 90
        if self.menu_idx == 2:
            offset = 5 if self.edit_mode else 0
            marker = ">>" if self.edit_mode else ">"
            oled.text(marker, marker_scale_x + offset, 0)
            oled.text(self.scale_list[self.edit_val] if self.edit_mode else self.scale_list[self.scale_idx], scale_x + offset, 0)
        else:
            oled.text(self.scale_list[self.scale_idx], scale_x, 0)
            
        # ----------- POZOSTAŁE WIERSZE --------------------
        y = 9
        marker_p = ">>" if self.edit_mode and self.menu_idx == 3 else (">" if self.menu_idx == 3 else " ")
        prob_txt = f"{marker_p}{int(self.edit_val*100) if self.edit_mode and self.menu_idx==3 else int(self.gate_probs[0]*100)}%"
        marker_l = ">>" if self.edit_mode and self.menu_idx == 6 else (">" if self.menu_idx == 6 else " ")
        len_txt = f"{marker_l}{self.edit_val if self.edit_mode and self.menu_idx==6 else self.gate_lens[0]}ms"
        oled.text("G1:", 0, y)
        oled.text(prob_txt, 28, y)
        oled.text(len_txt, 78, y)
        y = 17
        marker_p = ">>" if self.edit_mode and self.menu_idx == 4 else (">" if self.menu_idx == 4 else " ")
        prob_txt = f"{marker_p}{int(self.edit_val*100) if self.edit_mode and self.menu_idx==4 else int(self.gate_probs[1]*100)}%"
        marker_l = ">>" if self.edit_mode and self.menu_idx == 7 else (">" if self.menu_idx == 7 else " ")
        len_txt = f"{marker_l}{self.edit_val if self.edit_mode and self.menu_idx==7 else self.gate_lens[1]}ms"
        oled.text("G2:", 0, y)
        oled.text(prob_txt, 28, y)
        oled.text(len_txt, 78, y)
        y = 25
        marker_p = ">>" if self.edit_mode and self.menu_idx == 5 else (">" if self.menu_idx == 5 else " ")
        prob_txt = f"{marker_p}{int(self.edit_val*100) if self.edit_mode and self.menu_idx==5 else int(self.gate_probs[2]*100)}%"
        marker_l = ">>" if self.edit_mode and self.menu_idx == 8 else (">" if self.menu_idx == 8 else " ")
        len_txt = f"{marker_l}{self.edit_val if self.edit_mode and self.menu_idx==8 else self.gate_lens[2]}ms"
        oled.text("G3:", 0, y)
        oled.text(prob_txt, 28, y)
        oled.text(len_txt, 78, y)
        oled.show()

    def update_menu(self):
        if not self.edit_mode:
            idx = k2.range(len(self.menu_items))
            if idx != self.menu_idx:
                self.menu_idx = idx
                self.draw_menu(force=True)
        else:
            k2v = k2.percent()
            if self.menu_idx == 0:
                note_count = len(self.root_notes)
                total = note_count * (self.octave_max - self.octave_min + 1)
                idx = int(k2v * (total - 1) + 0.5)
                note_idx = idx % note_count
                octave = idx // note_count
                # Zmień tylko root (range zostaje, dopiero po zatwierdzeniu robimy korektę)
                if self.edit_val != (note_idx, octave):
                    self.edit_val = (note_idx, octave)
                    self.draw_menu(force=True)
            elif self.menu_idx == 1:
                # Edycja range: int 1..8
                range_val = int(self.range_min + k2v * (self.range_max - self.range_min) + 0.5)
                if self.edit_val != range_val:
                    self.edit_val = range_val
                    self.draw_menu(force=True)
            elif self.menu_idx == 2:
                new_idx = int(k2v * (len(self.scale_list) - 1) + 0.5)
                if self.edit_val != new_idx:
                    self.edit_val = new_idx
                    self.draw_menu(force=True)
            elif 3 <= self.menu_idx <= 5:
                new_val = round(k2v, 2)
                if self.edit_val != new_val:
                    self.edit_val = new_val
                    self.draw_menu(force=True)
            elif 6 <= self.menu_idx <= 8:
                new_len = int(10 + k2v * 990)
                if self.edit_val != new_len:
                    self.edit_val = new_len
                    self.draw_menu(force=True)

    def handle_b2(self):
        if not self.edit_mode:
            if self.menu_idx == 0:
                self.edit_val = (self.root_note_idx, self.root_octave)
            elif self.menu_idx == 1:
                self.edit_val = self.range_val
            elif self.menu_idx == 2:
                self.edit_val = self.scale_idx
            elif 3 <= self.menu_idx <= 5:
                self.edit_val = self.gate_probs[self.menu_idx - 3]
            elif 6 <= self.menu_idx <= 8:
                self.edit_val = self.gate_lens[self.menu_idx - 6]
            self.edit_mode = True
            self.draw_menu(force=True)
        else:
            if self.menu_idx == 0:
                self.root_note_idx, self.root_octave = self.edit_val
                # Korekta range, żeby suma nie przekroczyła 8
                self.range_val = max(self.range_min, min(self.range_max, 8 - self.root_octave))
            elif self.menu_idx == 1:
                self.range_val = self.edit_val
                # Korekta root_octave, żeby suma nie przekroczyła 8
                self.root_octave = max(self.octave_min, min(self.octave_max, 8 - self.range_val))
            elif self.menu_idx == 2:
                self.scale_idx = self.edit_val
            elif 3 <= self.menu_idx <= 5:
                self.gate_probs[self.menu_idx - 3] = self.edit_val
            elif 6 <= self.menu_idx <= 8:
                self.gate_lens[self.menu_idx - 6] = self.edit_val
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
            if utime.ticks_diff(now, last_menu_update) > 100:
                self.update_menu()
                last_menu_update = now

            clk = bool(din.value)
            if clk and not last_clock:
                self.handle_clock()
            last_clock = clk

            curr_b2 = b2.value()
            if curr_b2 and not last_b2:
                self.handle_b2()
            last_b2 = curr_b2

            self.update_gates()
            utime.sleep_ms(5)

script = SimpleBitGarden()
if __name__ == "__main__":
    script.main()
