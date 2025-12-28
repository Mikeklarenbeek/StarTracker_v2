from lib.as5048a import AS5048A
import time

# SPI1, maar SPI0 mag ook (dan pinnen aanpassen)
as5048 = AS5048A(
    spi_id=0,
    sck=2, mosi=3, miso=0, cs_pin=1
)

while True:
    data = as5048.read_all()
    print(data["angle_deg"])
    time.sleep(0.1)

from stepper import Stepper
import time

# --- Motor setup ---
# STEP=18, DIR=19, MS1=21, MS2=20, microstep=16, gear ratio 2:1
s1 = Stepper(
    step_pin=18,
    dir_pin=19,
    ms1_pin=21,
    ms2_pin=20,
    steps_per_rev=200,
    microstep=16,
    speed_sps=400,   # basis snelheid in stappen/sec
    gear_ratio=2.0
)

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

