from machine import Pin
from stepper import Stepper
import time

# --- Motor setup ---
# STEP=17, DIR=16, MS1=21, MS2=20, microstep=16, gear ratio 2:1
s1 = Stepper(
    step_pin=17,
    dir_pin=16,
    ms1_pin=21,
    ms2_pin=20,
    steps_per_rev=200,
    microstep=16,
    speed_sps=400,   # basis snelheid in stappen/sec
    gear_ratio=2.0
)
led = Pin(16, Pin.OUT) # Set up the onboard LED (can replace "LED" with a pin GPIO number)

led.value(1)  # Turn the LED ON
time.sleep(2) # Go to sleep for 2 seconds
        
led.value(0)  # Turn the LED OFF
time.sleep(2) # Go to sleep for 2 seconds

s1.enable(True)

# --- Beweeg naar 90 graden ---
print("Ga naar 90°")
s1.target_deg(90)
time.sleep(3)

# --- Beweeg terug naar 0 graden ---
print("Ga terug naar 0°")
s1.target_deg(0)
time.sleep(3)

# --- Free-run continu vooruit ---
print("Free-run vooruit, 1 rotatie/sec (output-as)")
s1.speed_rps(1)           # 1 rotatie per seconde op output-as
s1.free_run(direction=1)  # richting +1 = vooruit
time.sleep(3)

# --- Free-run continu achteruit met aangepaste snelheid ---
print("Free-run achteruit, 0.5 rotatie/sec")
s1.speed_rps(0.5)
s1.free_run(direction=-1) # richting -1 = achteruit
time.sleep(3)

# --- Stop motor ---
print("Stop motor")
s1.stop()

# --- Test directe step functies ---
print("Stap vooruit 10 stappen")
for _ in range(10):
    s1.step(1)
    time.sleep(0.01)

print("Stap achteruit 5 stappen")
for _ in range(5):
    s1.step(-1)
    time.sleep(0.01)

# --- Positie uitlezen ---
print("Huidige positie (stappen):", s1.get_pos())
print("Huidige positie (graden):", s1.get_pos_deg())

