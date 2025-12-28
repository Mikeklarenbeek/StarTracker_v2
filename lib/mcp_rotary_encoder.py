class MCPRotaryEncoder:
    def __init__(self, mcp, pin_a, pin_b, min_val=0, max_val=2):
        self.mcp = mcp
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.min_val = min_val
        self.max_val = max_val

        self.value = min_val
        self.last_state = self._read_state()

        # Geldige transitions
        self.transitions = {
            (0b00, 0b01): +1,
            (0b01, 0b11): +1,
            (0b11, 0b10): +1,
            (0b10, 0b00): +1,

            (0b00, 0b10): -1,
            (0b10, 0b11): -1,
            (0b11, 0b01): -1,
            (0b01, 0b00): -1,
        }

    def _read_state(self):
        a = self.mcp[self.pin_a].value()
        b = self.mcp[self.pin_b].value()
        return (a << 1) | b

    def update(self):
        state = self._read_state()

        if state != self.last_state:
            delta = self.transitions.get((self.last_state, state), 0)

            if delta != 0:
                self.value += delta

                # wrap-around
                if self.value > self.max_val:
                    self.value = self.min_val
                elif self.value < self.min_val:
                    self.value = self.max_val

            self.last_state = state

        return self.value
    def get_value(self):
        return self.value