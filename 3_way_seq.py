from europi import *
from europi_script import EuroPiScript
import random
import utime

SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
    "Pentatonic": [0, 2, 4, 7, 9]
}
SCALE_NAMES = list(SCALES.keys())

class TripleQuantizedProbGate(EuroPiScript):
    def __init__(self):
        # Parametry użytkownika
        self.gate_length_ms = 50
        self.cv_min = 0
        self.cv_max = 7
        self.scale_idx = 0
        self.base_note = 0
        self.gate_prob = [100, 100, 100]

        # Stan
        self.gate_state = [False, False, False]
        self.gate_timer = [0, 0, 0]

        # Menu
        self.menu_idx = 0
        self.menu_items = [
            "Gate length",
            "CV min",
            "CV max",
            "Scale",
            "Base note",
            "Gate 1 prob",
            "Gate 2 prob",
            "Gate 3 prob"
        ]
        self.edit_mode = False  # Czy edytujemy wartość?

        self.gate_out = [cv1, cv2, cv3]
        self.cv_out = [cv4, cv5, cv6]

        self.k1_last = k1.read_position()
        self.k2_last = k2.read_position()

        self.draw_menu()

    def draw_menu(self):
        oled.fill(0)
        for i, item in enumerate(self.menu_items):
            marker = ">" if i == self.menu_idx else " "
            edit = "*" if (self.edit_mode and i == self.menu_idx) else " "
            val = self.get_menu_value(i)
            oled.text(f"{marker}{item}:{val}{edit}", 0, i*8)
        oled.show()

    def get_menu_value(self, idx):
        if idx == 0:
            return f"{self.gate_length_ms}ms"
        elif idx == 1:
            return f"{self.cv_min}"
        elif idx == 2:
            return f"{self.cv_max}"
        elif idx == 3:
            return SCALE_NAMES[self.scale_idx]
        elif idx == 4:
            return str(self.base_note)
        elif 5 <= idx <= 7:
            return f"{self.gate_prob[idx-5]}%"
        return ""

    def quantize(self, note):
        scale = SCALES[SCALE_NAMES[self.scale_idx]]
        note_in_scale = scale[note % len(scale)]
        octave = note // len(scale)
        return self.base_note + note_in_scale + 12 * octave

    def handle_clock(self):
        for ch in range(3):
            if random.randint(1,100) <= self.gate_prob[ch]:
                note_num = random.randint(self.cv_min, self.cv_max)
                quantized_note = self.quantize(note_num)
                voltage = quantized_note / 12.0
                self.cv_out[ch].voltage(voltage)
                self.gate_out[ch].voltage(5)
                self.gate_state[ch] = True
                self.gate_timer[ch] = utime.ticks_add(utime.ticks_ms(), self.gate_length_ms)
            else:
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def update_gates(self):
        now = utime.ticks_ms()
        for ch in range(3):
            if self.gate_state[ch] and utime.ticks_diff(now, self.gate_timer[ch]) > 0:
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def handle_menu_navigation(self):
        # K1: zmiana menu_idx (tylko poza edycją)
        k1_pos = k1.read_position()
        if not self.edit_mode and k1_pos != self.k1_last:
            diff = k1_pos - self.k1_last
            if diff != 0:
                self.menu_idx = (self.menu_idx + diff) % len(self.menu_items)
                self.draw_menu()
            self.k1_last = k1_pos

        # K2: zmiana wartości (tylko w trybie edycji)
        k2_pos = k2.read_position()
        if self.edit_mode and k2_pos != self.k2_last:
            diff = k2_pos - self.k2_last
            if diff != 0:
                self.change_value(self.menu_idx, diff)
                self.draw_menu()
            self.k2_last = k2_pos

    def change_value(self, idx, step):
        if idx == 0:
            self.gate_length_ms = min(999, max(1, self.gate_length_ms + 10*step))
        elif idx == 1:
            self.cv_min = min(self.cv_max, max(0, self.cv_min + step))
        elif idx == 2:
            self.cv_max = max(self.cv_min, min(7, self.cv_max + step))
        elif idx == 3:
            self.scale_idx = (self.scale_idx + step) % len(SCALE_NAMES)
        elif idx == 4:
            self.base_note = (self.base_note + step) % 12
        elif 5 <= idx <= 7:
            ch = idx - 5
            self.gate_prob[ch] = min(100, max(0, self.gate_prob[ch] + 5*step))

    def main(self):
        last_clock = False
        while True:
            # Przycisk b1: ENTER/wyjdź z edycji
            if b1.read():
                self.edit_mode = not self.edit_mode
                self.draw_menu()
                utime.sleep_ms(250)

            self.handle_menu_navigation()

            clk = digitalin.read() > 0.5
            if clk and not last_clock:
                self.handle_clock()
            last_clock = clk

            self.update_gates()
            utime.sleep_ms(5)

script = TripleQuantizedProbGate()
