"""
AS5048A Magnetic Encoder Library for MicroPython
------------------------------------------------

Compatible with: Raspberry Pi Pico / Pico W (MicroPython)

This library reads angle, total rotations, RPM and normalized angles
from the AMS AS5048A 14-bit magnetic rotary encoder using SPI.

Usage example
-------------

from as5048a import AS5048A
import time

enc = AS5048A(cs_pin=17, spi_id=0)   # Default pins for SPI0 on Pico W

while True:
    enc.update()  # read and process new data
    print("Angle:", enc.angle_deg)
    print("Corrected:", enc.corrected_angle)
    print("Turns:", enc.turns)
    print("Total angle:", enc.total_angle)
    print("RPM:", enc.rpm)
    time.sleep(0.25)

-------------------------------------------------------------

API Overview
============

Class AS5048A(cs_pin=17, spi_id=0, baudrate=3000000)
----------------------------------------------------
Create a new AS5048A encoder instance.

Parameters:
    cs_pin   : GPIO pin number of chip select
    spi_id   : SPI interface (0 or 1)
    baudrate : SPI clock speed (default 3 MHz)

Properties (read-only):
    angle_deg        : Current angle 0–360°
    corrected_angle  : Angle minus start reference (tared)
    turns            : Integer number of full rotations
    total_angle      : Continuous angle (turns * 360 + corrected)
    rpm              : Computed rotations per minute

Methods:
    update()         : Reads the sensor + updates angle, turns & rpm
    read_raw()       : Reads raw 14-bit encoder value
    reset_zero()     : Sets current position as new zero reference
    set_start_angle(deg) : Manually set tare offset
"""

from machine import Pin, SPI
import time


class AS5048A:
    """Driver for AS5048A magnetic rotary encoder (SPI)."""

    READ_CMD = 0xFFFF  # Read command for AS5048A

    def __init__(self, cs_pin=17, spi_id=0, baudrate=3000000):
        # --- Chip Select pin ---
        self.cs = Pin(cs_pin, Pin.OUT)
        self.cs.value(1)

        # --- SPI interface ---
        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=1,
            phase=1,
            bits=8,
            firstbit=SPI.MSB
        )

        # --- State tracking ---
        self.angle_deg = 0.0
        self.corrected_angle = 0.0
        self.start_angle = 0.0
        self.turns = 0
        self.previous_quadrant = None
        self.total_angle = 0.0

        # RPM tracking
        self._rpm_timer = time.ticks_ms()
        self._rpm_counter = 0
        self.rpm = 0.0

        # Read initial angle
        self.update()
        self.start_angle = self.angle_deg

    # ------------------------------
    #  LOW-LEVEL SPI COMMUNICATION
    # ------------------------------
    def _transfer16(self, value):
        """Transfers a 16-bit command over SPI (big-endian)."""
        buf = value.to_bytes(2, 'big')
        self.cs.value(0)
        self.spi.write(buf)
        rx = self.spi.read(2)
        self.cs.value(1)
        return int.from_bytes(rx, 'big')

    def read_raw(self):
        """Reads raw 14-bit angle from AS5048A (0 - 16383)."""
        # Send read command
        self._transfer16(self.READ_CMD)
        time.sleep_us(50)
        raw = self._transfer16(self.READ_CMD)

        # Mask top 2 bits (PAR + EF)
        return raw & 0x3FFF

    # ------------------------------
    #  ANGLE PROCESSING
    # ------------------------------
    def _compute_angle(self):
        raw = self.read_raw()
        self.angle_deg = (raw / 16384.0) * 360.0

    def _compute_corrected(self):
        self.corrected_angle = self.angle_deg - self.start_angle
        if self.corrected_angle < 0:
            self.corrected_angle += 360

    def _quadrant(self, angle):
        if 0 <= angle <= 90:
            return 1
        if 90 < angle <= 180:
            return 2
        if 180 < angle <= 270:
            return 3
        return 4

    def _update_turns(self):
        q = self._quadrant(self.corrected_angle)

        if self.previous_quadrant is not None:
            # 4 → 1 means CW
            if q == 1 and self.previous_quadrant == 4:
                self.turns += 1
                self._rpm_counter += 1

            # 1 → 4 means CCW
            elif q == 4 and self.previous_quadrant == 1:
                self.turns -= 1
                self._rpm_counter -= 1

        self.previous_quadrant = q

    def _update_total_angle(self):
        self.total_angle = self.turns * 360 + self.corrected_angle

    # ------------------------------
    #  RPM CALCULATION
    # ------------------------------
    def _update_rpm(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._rpm_timer) >= 15000:  # 15 seconds
            self.rpm = (self._rpm_counter * 4)  # extrapolate to 60 sec
            self._rpm_counter = 0
            self._rpm_timer = now

    # ------------------------------
    #  PUBLIC UPDATE FUNCTION
    # ------------------------------
    def update(self):
        """Reads encoder and updates angle, turns & rpm."""
        self._compute_angle()
        self._compute_corrected()
        self._update_turns()
        self._update_total_angle()
        self._update_rpm()

    # ------------------------------
    #  USER FUNCTIONS
    # ------------------------------
    def reset_zero(self):
        """Set the current angle as new zero reference."""
        self.start_angle = self.angle_deg

    def set_start_angle(self, deg):
        """Manually set reference angle in degrees."""
        self.start_angle = deg
