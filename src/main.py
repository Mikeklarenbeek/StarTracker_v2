from machine import Pin
from utime import sleep

pin = Pin("LED", Pin.OUT)

while True:
    try:
        pin.toggle()
        sleep(1) # sleep 1sec
    except KeyboardInterrupt:
        break
pin.off()
print("Finished.")
