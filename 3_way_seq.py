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
        return self

