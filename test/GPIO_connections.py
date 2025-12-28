
#NEMA 17
from lib.stepper import Stepper

s1 = Stepper(
    en_pin=6,
    step_pin=9,
    dir_pin=10,
    ms1_pin=7,
    ms2_pin=8,
    steps_per_rev=200,
    microstep=16,
    speed_sps=400,   # basis snelheid in stappen/sec
    gear_ratio=2.0
)
s1.enable(True)

s2 = Stepper(
    en_pin=11,
    step_pin=12,
    dir_pin=13,
    ms1_pin=7,
    ms2_pin=8,
    steps_per_rev=200,
    microstep=16,
    speed_sps=400,   # basis snelheid in stappen/sec
    gear_ratio=2.0
)
s2.enable(True)

#ST3215
from machine import UART, Pin
from lib.st3215 import ST3215
import time
uart = UART(1, baudrate=1000000, tx=Pin(4), rx=Pin(5))
servo = ST3215(tx_pin=4, rx_pin=5, uart_id=1, baudrate=1000000, timeout=50)
ids = servo.ListServos()
print("Servo's:", ids)

#AS5048A
from lib.as5048a import AS5048A
from machine import Pin, SPI
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, sck=Pin(2), mosi=Pin(3), miso=Pin(16))
as5048 = AS5048A(spi=spi, cs_pin=Pin(1))

#MPU6050
import machine
from lib.mpu6050 import MPU6050
i2c = machine.I2C(1, scl=machine.Pin(17), sda=machine.Pin(16), freq=100000)
mpu = MPU6050(bus=i2c, addr=0x68)

#QMC5883L
from lib.qmc5883L import QMC5883
i2c = machine.I2C(1, scl=machine.Pin(17), sda=machine.Pin(16), freq=100000)
mag = QMC5883(i2c, irq=False, slvAddr=0x0D, autoScale=True)

#mcp23017
from machine import Pin, I2C
import lib.mcp23017 as mcp23017
i2c = I2C(scl=Pin(15), sda=Pin(14), freq=100000)
mcp = mcp23017.MCP23017(i2c, 0x20)

#limit switch module
LIMIT_SWITCH_PIN = 26
limit_switch = machine.Pin(LIMIT_SWITCH_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# limitswitch
from machine import Pin
LIMIT_SWITCH_ncPIN = 27
limit_switch_nc = Pin(LIMIT_SWITCH_ncPIN, Pin.IN, Pin.PULL_UP)

