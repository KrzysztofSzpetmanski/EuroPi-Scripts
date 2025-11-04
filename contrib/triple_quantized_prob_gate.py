from europi import *
from europi_script import EuroPiScript
import random
import utime

# Musical scales for quantization - can be extended with additional scales
SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
    "Pentatonic": [0, 2, 4, 7, 9]
}
SCALE_NAMES = list(SCALES.keys())

class TripleQuantizedProbGate(EuroPiScript):
    """
    Triple Channel Probabilistic Gate + CV Generator with Quantizer and Configuration Menu
    
    Features:
    - Listens for clock triggers on digital input
    - Generates 3 pairs of gate and CV outputs on each clock cycle:
      * Gates: outputs 1-3 (cv1, cv2, cv3)
      * CVs: outputs 4-6 (cv4, cv5, cv6)
    - Configurable gate length in milliseconds
    - Configurable CV note range (0-7V, V/Oct standard)
    - Independent probability settings for each channel (0-100%)
    - Quantizer with selectable scales and base notes
    - Menu navigation via b1/b2/b3 buttons
    """
    
    def __init__(self):
        # --- User-configurable parameters ---
        self.gate_length_ms = 50    # Gate signal duration in milliseconds
        self.cv_min = 0             # Minimum note value (V/Oct scale, 0 = 0V)
        self.cv_max = 7             # Maximum note value (7 = 7V)
        self.scale_idx = 0          # Index of selected scale from SCALE_NAMES
        self.base_note = 0          # Base note offset (e.g., C=0, D=2, etc.)
        self.gate_prob = [100, 100, 100]  # Gate probability for each channel (0-100%)

        # --- Output state variables ---
        self.gate_state = [False, False, False]    # Current gate state (True/False) for each channel
        self.gate_timer = [0, 0, 0]                # Gate turn-off timestamp (ms) for each channel

        # --- Configuration menu ---
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

        # --- Output assignment for clarity ---
        self.gate_out = [cv1, cv2, cv3]   # Gate outputs (three channels)
        self.cv_out = [cv4, cv5, cv6]     # CV outputs (three channels)

        # Display menu at startup
        self.draw_menu()

    def draw_menu(self):
        """
        Draws the configuration menu on the OLED display showing all options and their current values.
        """
        oled.clear()
        for i, item in enumerate(self.menu_items):
            # Mark current selection with ">"
            marker = ">" if i == self.menu_idx else " "
            val = self.get_menu_value(i)
            oled.text(f"{marker}{item}: {val}", 0, i*8)
        oled.show()

    def get_menu_value(self, idx):
        """
        Returns the display value for a given menu option.
        
        Args:
            idx: Menu item index
            
        Returns:
            String representation of the current value for the menu item
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
        Handles button press events for menu navigation and parameter editing:
        - b1: Navigate to next menu option
        - b2: Increase current parameter value
        - b3: Decrease current parameter value
        
        Args:
            btn: Button object that was pressed (b1, b2, or b3)
        """
        if btn == b1:
            # Navigate to next menu item (circular)
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
            self.draw_menu()
        elif btn == b2:
            # Increase parameter value
            idx = self.menu_idx
            if idx == 0:  # Gate length
                self.gate_length_ms = min(999, self.gate_length_ms + 10)
            elif idx == 1:  # CV min
                self.cv_min = min(self.cv_max, self.cv_min + 1)
            elif idx == 2:  # CV max
                self.cv_max = max(self.cv_min, min(7, self.cv_max + 1))
            elif idx == 3:  # Scale
                self.scale_idx = (self.scale_idx + 1) % len(SCALE_NAMES)
            elif idx == 4:  # Base note
                self.base_note = (self.base_note + 1) % 12
            elif 5 <= idx <= 7:  # Gate probabilities
                ch = idx - 5
                self.gate_prob[ch] = min(100, self.gate_prob[ch] + 5)
            self.draw_menu()
        elif btn == b3:
            # Decrease parameter value
            idx = self.menu_idx
            if idx == 0:  # Gate length
                self.gate_length_ms = max(1, self.gate_length_ms - 10)
            elif idx == 1:  # CV min
                self.cv_min = max(0, self.cv_min - 1)
            elif idx == 2:  # CV max
                self.cv_max = max(self.cv_min, self.cv_max - 1)
            elif idx == 3:  # Scale
                self.scale_idx = (self.scale_idx - 1) % len(SCALE_NAMES)
            elif idx == 4:  # Base note
                self.base_note = (self.base_note - 1) % 12
            elif 5 <= idx <= 7:  # Gate probabilities
                ch = idx - 5
                self.gate_prob[ch] = max(0, self.gate_prob[ch] - 5)
            self.draw_menu()

    def quantize(self, note):
        """
        Quantizer: Converts a note number to a value conforming to the selected scale and key.
        
        Args:
            note: Input note number
            
        Returns:
            Quantized note value (semitone number)
        """
        scale = SCALES[SCALE_NAMES[self.scale_idx]]
        note_in_scale = scale[note % len(scale)]
        octave = note // len(scale)
        # Return semitone number (0-11) + base note offset + octave
        return self.base_note + note_in_scale + 12 * octave

    def handle_clock(self):
        """
        Handles rising edge of clock signal from digital input (trigger/clock).
        For each channel:
        - Randomly determine if gate should occur (based on probability)
        - If yes, randomly select note, quantize it, and send CV and gate signals
        """
        for ch in range(3):
            # Check if gate should trigger based on probability
            if random.randint(1, 100) <= self.gate_prob[ch]:
                # Generate random note within configured range
                note_num = random.randint(self.cv_min, self.cv_max)
                quantized_note = self.quantize(note_num)
                voltage = quantized_note / 12.0  # Convert to V/Oct
                
                # Send CV and gate signals
                self.cv_out[ch].voltage(voltage)    # Send CV to output
                self.gate_out[ch].voltage(5)        # Set gate to 5V
                self.gate_state[ch] = True
                self.gate_timer[ch] = utime.ticks_add(utime.ticks_ms(), self.gate_length_ms)
            else:
                # No gate on this channel for this clock cycle
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def update_gates(self):
        """
        Checks if any gates should be turned off (after gate_length_ms has elapsed).
        """
        now = utime.ticks_ms()
        for ch in range(3):
            if self.gate_state[ch] and utime.ticks_diff(now, self.gate_timer[ch]) > 0:
                self.gate_out[ch].voltage(0)
                self.gate_state[ch] = False

    def main(self):
        """
        Main program loop:
        - Handle button presses for menu navigation
        - Detect clock edges on digital input
        - Manage gate timing
        """
        last_clock = False
        
        while True:
            # Handle button presses (menu navigation)
            if b1.read():
                self.on_button_press(b1)
                utime.sleep_ms(250)  # Debounce delay
            if b2.read():
                self.on_button_press(b2)
                utime.sleep_ms(250)
            if b3.read():
                self.on_button_press(b3)
                utime.sleep_ms(250)

            # Detect rising edge on clock input (digital in)
            clk = digitalin.read() > 0.5
            if clk and not last_clock:
                self.handle_clock()  # Trigger action on rising edge
            last_clock = clk

            # Update gate states (turn off expired gates)
            self.update_gates()
            utime.sleep_ms(5)  # Short delay to save CPU cycles

# Launch the script
script = TripleQuantizedProbGate()