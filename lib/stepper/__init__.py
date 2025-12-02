import machine
import time
import math

# Correcte MS1/MS2 mapping voor TMC2209 standalone mode
MICROSTEPPING_MODES = {
    1:  (0, 0),
    2:  (1, 0),
    4:  (0, 1),
    8:  (1, 1),
    16: (1, 1),  # TMC2209 ondersteunt 1/16 via MS1+MS2
}

MICROSTEP_FACTORS = {
    1: 1,
    2: 2,
    4: 4,
    8: 8,
    16: 16,
}

class Stepper:
    def __init__(self, step_pin, dir_pin, ms1_pin=None, ms2_pin=None, en_pin=None,
                 steps_per_rev=200, microstep=1, speed_sps=200, invert_dir=False,
                 gear_ratio=1.0):
        # Pins
        self.step_pin = machine.Pin(step_pin, machine.Pin.OUT)
        self.dir_pin  = machine.Pin(dir_pin,  machine.Pin.OUT)
        self.en_pin   = machine.Pin(en_pin, machine.Pin.OUT) if en_pin is not None else None
        self.ms1 = machine.Pin(ms1_pin, machine.Pin.OUT) if ms1_pin is not None else None
        self.ms2 = machine.Pin(ms2_pin, machine.Pin.OUT) if ms2_pin is not None else None

        # Motor params
        self.steps_per_rev_base = steps_per_rev
        self.microstep = microstep
        self.steps_per_rev = steps_per_rev * microstep
        self.gear_ratio = gear_ratio  # ratio: output rotations per motor rotation

        # Motion
        self.speed_sps = speed_sps
        self.pos = 0
        self.target_pos = 0
        self.invert_dir = invert_dir
        self.enabled = True
        self.free_direction = 0  # vrije richting, 0 = geen free run

        # Stel microstepping pinnen in
        self.set_microstepping(self.microstep)

        # Timer
        self.timer = machine.Timer()
        self._start_timer()

    # ---------------- MICROSTEPPING ----------------
    def set_microstepping(self, mode):
        if mode not in MICROSTEP_FACTORS:
            print("Ongeldige microstepping:", mode)
            return False

        self.microstep = MICROSTEP_FACTORS[mode]
        self.steps_per_rev = self.steps_per_rev_base * self.microstep

        # Stel MS1/MS2 pinnen in indien aanwezig
        if self.ms1 and self.ms2:
            ms1_val, ms2_val = MICROSTEPPING_MODES.get(mode, (0, 0))
            self.ms1.value(ms1_val)
            self.ms2.value(ms2_val)

        print(f"Microstepping ingesteld op {mode}x → {self.steps_per_rev} steps/rev")
        return True

    # ---------------- SPEED ----------------
    def speed(self, sps):
        self.speed_sps = sps
        self._restart_timer()

    def speed_rps(self, rps):
        sps = rps * self.steps_per_rev * self.gear_ratio
        self.speed(sps)

    # ---------------- TIMER ----------------
    def _start_timer(self):
        if self.speed_sps <= 0:
            return
        self.timer.init(freq=int(self.speed_sps), mode=machine.Timer.PERIODIC, callback=self._step_event)

    def _restart_timer(self):
        self.timer.deinit()
        self._start_timer()

    # ---------------- STEP EVENT ----------------
    def _step_event(self, t):
        if not self.enabled:
            return

        # Free run prioriteit
        if self.free_direction != 0:
            self._step(self.free_direction)
            return

        # Anders naar target
        if self.target_pos > self.pos:
            self._step(1)
        elif self.target_pos < self.pos:
            self._step(-1)

    # ---------------- STEP ----------------
    def _step(self, direction):
        if direction > 0:
            self.dir_pin.value(1 ^ self.invert_dir)
            self.pos += 1
        elif direction < 0:
            self.dir_pin.value(0 ^ self.invert_dir)
            self.pos -= 1

        # Pulse
        self.step_pin.value(1)
        time.sleep_us(2)  # minimale pulse voor TMC2209
        self.step_pin.value(0)

    def step(self, d):
        self._step(d)

    # ---------------- TARGET ----------------
    def target(self, t):
        self.target_pos = int(t)
        self.free_direction = 0  # stop free run

    def target_deg(self, deg):
        steps = deg * self.steps_per_rev * self.gear_ratio / 360.0
        self.target(steps)

    def target_rad(self, rad):
        steps = rad * self.steps_per_rev * self.gear_ratio / (2 * math.pi)
        self.target(steps)

    # ---------------- FREE RUN ----------------
    def free_run(self, direction, sps=None):
        """
        direction = +1 (vooruit) of -1 (achteruit)
        sps = optioneel, snelheid in stappen/sec
        """
        self.free_direction = direction
        if sps is not None:
            self.speed_sps = abs(sps)
            self._restart_timer()

    # ---------------- STOP ----------------
    def stop(self):
        self.free_direction = 0
        self.timer.deinit()

    # ---------------- ENABLE ----------------
    def enable(self, e):
        if self.en_pin:
            self.en_pin.value(0 if e else 1)  # LOW = enabled
        self.enabled = e

    def is_enabled(self):
        return self.enabled

    # ---------------- POSITION ----------------
    def get_pos(self):
        return self.pos

    def get_pos_deg(self):
        return self.pos * 360.0 / (self.steps_per_rev * self.gear_ratio)

    def get_pos_rad(self):
        return self.pos * 2 * math.pi / (self.steps_per_rev * self.gear_ratio)

    def overwrite_pos(self, p):
        self.pos = int(p)

    def overwrite_pos_deg(self, deg):
        steps = deg * self.steps_per_rev * self.gear_ratio / 360.0
        self.overwrite_pos(steps)

    def overwrite_pos_rad(self, rad):
        steps = rad * self.steps_per_rev * self.gear_ratio / (2 * math.pi)
        self.overwrite_pos(steps)
