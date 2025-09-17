from europi import *
from europi_script import EuroPiScript
import random
import utime

# Przykładowe skale — można rozbudować o kolejne
SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
    "Pentatonic": [0, 2, 4, 7, 9]
}
SCALE_NAMES = list(SCALES.keys())

class TripleQuantizedProbGate(EuroPiScript):
    """
    Klasa główna obsługująca 3 kanały gate + CV z quantizerem i menu konfiguracji.
    """
    def __init__(self):
        # --- Parametry konfigurowalne przez użytkownika ---
        self.gate_length_ms = 50    # Czas trwania sygnału gate (w ms)
        self.cv_min = 0             # Minimalna wartość nuty (skala V/Oct, 0 = 0V)
        self.cv_max = 7             # Maksymalna wartość nuty (7 = 7V)
        self.scale_idx = 0          # Indeks wybranej skali z listy SCALE_NAMES
        self.base_note = 0          # Przesunięcie podstawowej nuty (np. C=0, D=2, itd.)
        self.gate_prob = [100, 100, 100]  # Prawdopodobieństwo wystąpienia gate (każdy kanał osobno, w %)

        # --- Zmienne stanu wyjść ---
        self.gate_state = [False, False, False]    # Czy gate jest obecnie aktywny (True/False) dla każdego kanału
        self.gate_timer = [0, 0, 0]                # Czas wyłączenia gate (timestamp w ms)

        # --- Menu konfiguracji ---
        self.menu_idx = 0
        self.menu_items = [
            "Gate length",    # 0
            "CV min",         # 1
            "CV max",         # 2
            "Scale",          # 3
            "Base note",      # 4
            "Gate 1 prob",    # 5
            "Gate 2 prob",    # 6
            "Gate 3 prob"     # 7
        ]

        # --- Przypisanie wyjść do kanałów (dla czytelności) ---
        self.gate_out = [cv1, cv2, cv3]   # Wyjścia gate (trzy kanały)
        self.cv_out = [cv4, cv5, cv6]     # Wyjścia CV (trzy kanały)

        self.draw_menu()  # Wyświetl menu przy starcie

    def draw_menu(self):
        """
        Rysuje menu na wyświetlaczu OLED — pokazuje wszystkie opcje i ich aktualne wartości.
        """
        oled.clear()
        for i, item in enumerate(self.menu_items):
            marker = ">" if i == self.menu_idx else " "
            val = self.get_menu_value(i)
            oled.text(f"{marker}{item}: {val}", 0, i*8)
        oled.show()

    def get_menu_value(self, idx):
        """
        Zwraca wartość danej opcji menu do wyświetlenia.
        """
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

    def on_button_press(self, btn):
        """
        Obsługuje wciśnięcia przycisków (menu):
        - b1: przeskok do kolejnej opcji menu
        - b2: zwiększenie wartości
        - b3: zmniejszenie wartości
        """
        if btn == b1:
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
            self.draw_menu()
        elif btn == b2:
            idx = self.menu_idx
            if idx == 0:
                self.gate_length_ms = min(999, self.gate_length_ms + 10)
            elif idx == 1:
                self.cv_min = min(self.cv_max, self.cv_min + 1)
            elif idx == 2:
                self.cv_max = max(self.cv_min, min(7, self.cv_max + 1))
            elif idx == 3:
                self.scale_idx = (self.scale_idx + 1) % len(SCALE_NAMES)
            elif idx == 4:
                self.base_note = (self.base_note + 1) % 12
            elif 5 <= idx <= 7:
                ch = idx - 5
                self.gate_prob[ch] = min(100, self.gate_prob[ch] + 5)
            self.draw_menu()
        elif btn == b3:
            idx = self.menu_idx
            if idx == 0:
                self.gate_length_ms = max(1, self.gate_length_ms - 10)
            elif idx == 1:
                self.cv_min = max(0, self.cv_min - 1)
            elif idx == 2:
                self.cv_max = max(self.cv_min, self.cv_max - 1)
            elif idx == 3:
                self.scale_idx = (self.scale_idx - 1) % len(SCALE_NAMES)
            elif idx == 4:
                self.base_note = (self.base_note - 1) % 12
            elif 5 <= idx <= 7:
                ch = idx - 5
                self.gate_prob[ch] = max(0, self.gate_prob[ch] - 5)
            self.draw_menu()

    def quantize(self, note):
        """
        Quantizer: zamienia numer nuty na wartość zgodną z wybraną skalą i tonacją.
        """
        scale = SCALES[SCALE_NAMES[self.scale_idx]]
        note_in_scale = scale[note % len(scale)]
        octave = note // len(scale)
        # Zwraca numer półtonu (0-11) + przesunięcie + oktawa
        return self.base_note + note_in_scale + 12 * octave

    def handle_clock(self):
        """
        Obsługa narastającego zbocza zegara z wejścia digital in (trigger/clock):
        Dla każdego kanału:
        - losuj, czy gate ma się pojawić (probability)
        - jeśli tak, losuj nutę, quantizuj, wyślij CV i gate
        """
        for ch in range(3):
            if random.randint(1,100) <= self.gate_prob[ch]:
                # Losowanie numeru nuty w zadanym zakresie
                note_num = random.randint(self.cv_min, self.cv_max)
                quantized_note = self.quantize(note_num)
                voltage = quantized_note / 12.0 # przelicz na V/Oct
                self.cv_out[ch].voltage(voltage)    # Wyślij CV na wyjście
                self.gate_out[ch].voltage(5)        # Ustaw gate na 5V
                self.gate_state[ch] = True
                self.gate_timer[ch] = utime.ticks_add(utime.ticks_ms(), self.gate_length_ms)
            else:
                # Gate nie występuje na tym kanale w tej iteracji
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def update_gates(self):
        """
        Sprawdza, czy należy już wyłączyć gate (po upływie gate_length_ms).
        """
        now = utime.ticks_ms()
        for ch in range(3):
            if self.gate_state[ch] and utime.ticks_diff(now, self.gate_timer[ch]) > 0:
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def main(self):
        """
        Główna pętla programu:
        - obsługa przycisków do menu
        - detekcja zbocza zegara na digital in
        - obsługa czasów gate
        """
        last_clock = False
        while True:
            # Obsługa przycisków (menu)
            if b1.read():
                self.on_button_press(b1)
                utime.sleep_ms(250)  # Debounce
            if b2.read():
                self.on_button_press(b2)
                utime.sleep_ms(250)
            if b3.read():
                self.on_button_press(b3)
                utime.sleep_ms(250)

            # Detekcja narastającego zbocza na wejściu zegara (digital in)
            clk = digitalin.read() > 0.5
            if clk and not last_clock:
                self.handle_clock()  # Akcja na każde zbocze narastające
            last_clock = clk

            self.update_gates()      # Kontrola wygaszania gate po czasie
            utime.sleep_ms(5)       # Krótka przerwa (oszczędza CPU)

# Uruchomienie skryptu
script = TripleQuantizedProbGate()
