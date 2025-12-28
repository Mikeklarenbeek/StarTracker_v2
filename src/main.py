from machine import UART, Pin
from st3215 import ST3215
import time

# UART1, GP4=TX, GP5=RX
uart = UART(1, baudrate=1000000, tx=Pin(4), rx=Pin(5))
servo = ST3215(uart)

ids = servo.ListServos()
print("Servo's:", ids)

if ids:
    servo.MoveTo(ids[0], 2048)
    time.sleep(2)
    pos = servo.ReadPosition(ids[0])
    print("Huidige positie:", pos)