class FrameException(Exception):
    def __init__(self, msg, data = None, timeout = False):
        self.message = msg
        self.timeout = timeout
        if data is not None:
            self.message += " Data: '" + repr(data) + "'"
        super().__init__(self.message)

class CommuncationException(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

class ST3215:
    # (adr, length, signed)
    FW_MAJOR = (0x00, 1, False)
    FW_MINOR = (0x01, 1, False)
    SERVO_MAJOR = (0x03, 1, False)
    SERVO_MINOR = (0x04, 1, False)
    ID = (0x05, 1, False)
    BAUDRATE = (0x06, 1, False)
    RETURN_DELAY = (0x07, 1, False)
    RESPONSE_STATUS_LEVEL = (0x08, 1, False)
    MIN_ANGLE = (0x09, 2, False)
    MAX_ANGLE = (0x0B, 2, False)
    MAX_TEMPERATURE = (0x0D, 1, False)
    MAX_INPUT_VOLTAGE = (0x0E, 1, False)
    MAX_TORQUE = (0x10, 1, False)
    PHASE = (0x12, 1, False)
    UNLOADING_COND = (0x13, 1, False)
    LED_ALARM_COND = (0x14, 1, False)
    POSITION_LOOP_P = (0x15, 1, False)
    POSITION_LOOP_D = (0x16, 1, False)
    POSITION_LOOP_I = (0x17, 1, False)
    CW_INSENSITIVE_ZONE = (0x1A, 1, False)
    CCW_INSENSITIVE_ZONE = (0x1B, 1, False)
    PROTECTION_CURRENT = (0x1C, 2, False)
    ANGLE_RESOLUTUION = (0x1E, 1, False)
    POSITION_CORRECTION = (0x1F, 2, True)
    OPERATION_MODE = (0x21, 1, False)
    PROTECTION_TORQUE = (0x22, 1, False)
    PROTECTION_TIME = (0x23, 1, False)
    OVERLOAD_TORQUE = (0x24, 1, False)
    SPEED_CLOSED_LOOP_P = (0x25, 1, False)
    OVERCURRENT_PROT_TIME = (0x26, 1, False)
    VELOCITY_CLOSED_LOOP_I = (0x27, 1, False)
    TORQUE_SWITCH = (0x28, 1, False)
    ACCELERATION = (0x29, 1, False)
    TARGET_LOCATION = (0x2A, 2, True)
    OPERATION_TIME = (0x2C, 2, False)
    OPERATION_SPEED = (0x2E, 2, False)
    TORQUE_LIMIT = (0x30, 2, False)
    LOCK_FLAG = (0x37, 1, False)
    CURRENT_LOCATION = (0x38, 2, False)
    CURRENT_SPEED = (0x3A, 2, False)
    CURRENT_LOAD = (0x3C, 2, False)
    CURRENT_VOLTAGE = (0x3E, 1, False)
    CURRENT_TEMPERATURE = (0x3F, 1, False)
    ASYC_WRITE_FLAG = (0x40, 1, False)
    SERVO_STATUS = (0x41, 1, False)
    MOVE_FLAG = (0x42, 1, False)
    CURRENT_CURRENT = (0x45, 2, False)

    def __init__(self,uart):
        self.servo = SerialServo(uart)

    def ReadRegister(self, id, reg):
        adr = reg[0]
        l = reg[1]
        signed = reg[2]
        if l == 2:
            return self.servo.ReadWord(id, adr, signed)
        else:
            return self.servo.ReadChar(id, adr)

    def WriteRegister(self, id, reg, value):
        adr = reg[0]
        l = reg[1]
        if l == 2:
            return self.servo.WriteWord(id, adr, value)
        else:
            return self.servo.WriteChar(id, adr, value)

    def Ping(self, id):
        return self.servo.Ping(id)
    
    def EepromLock(self, id):
        return self.servo.WriteChar(self.LOCK_FLAG[0], 1)

    def EepromUnlock(self, id):
        return self.servo.WriteChar(self.LOCK_FLAG[0], 0)
    
class SerialServo:
    PING = 0x01
    READDATA = 0x02
    WRITEDATA = 0x03
    REGWRITEDATA = 0x04
    ACTION = 0x05
    SYNCREADDATA = 0x82
    SYNCWRITEDATA = 0x83
    RESET = 0x06

    COMM_SUCCESS = 0  # tx or rx packet communication success
    COMM_PORT_BUSY = -1  # Port is busy (in use)
    COMM_TX_FAIL = -2  # Failed transmit instruction packet
    COMM_RX_FAIL = -3  # Failed get status packet
    COMM_TX_ERROR = -4  # Incorrect instruction packet
    COMM_RX_WAITING = -5  # Now recieving status packet
    COMM_RX_TIMEOUT = -6  # There is no status packet
    COMM_RX_CORRUPT = -7  # Incorrect status packet
    COMM_NOT_AVAILABLE = -9  #

    def __init__(self, uart):
        self.uart = uart

    def Ping(self, id):
        self.sendframe(id, self.PING)
        try:
            (id, reply, params) = self.readframe()
            if id == id and reply == self.COMM_SUCCESS:
                return True
            else:
                return False
        except FrameException as x:
            print("Error during Ping: " + x.message)
            return False


    def WriteWord(self, id, address, value):
        return self.WriteData(id, address, value.to_bytes(2, "little"))

    def ReadWord(self, id, address, signed=False):
        data = self.ReadData(id,address, 2)
        value = int(data[0]) + (int(data[1]) << 8)
        if signed:
            return -65536 + value
        else:
            return value

    def WriteChar(self, id, address, value):
        return self.WriteData(id, address, value.to_bytes(1))
    
    def ReadChar(self, id, address):
        data = self.ReadData(id,address, 1)
        return int(data)

    def WriteData(self, id, address, data):
        params = bytearray((address & 0xFF,))
        for d in data:
            params.append(d)
        self.sendframe(id, self.WRITEDATA, params)
        try:
            (rid, status, data) = self.readframe()
            if rid == id:
                if status == self.COMM_SUCCESS:
                    return True
            return False
        except FrameException as x:
            if x.timeout:
                return False
            else:
                raise x

    def ReadData(self, id, address, length):
        params = bytes((address & 0xFF, length & 0xFF))
        self.sendframe(id, self.READDATA, params)
        (rid, status, data) = self.readframe()
        if rid == id:
            if status == self.COMM_SUCCESS:
                return data
            else:
                raise CommuncationException(f"Error during transaction. Status code {status}'")
        else:
            raise CommuncationException(f"Reply from different id ({rid}) than target ({id})")

    def checksum(self, framedata):
        sum = 0
        for b in framedata:
            sum += b
        cs = ~(sum) & 0xFF
        return cs

    def sendframe(self, id, instruction, parameters = b''):
        frame = bytearray(b'\xFF\xFF')
        frame.append(id & 0xFF)
        frame.append(len(parameters) + 2)
        frame.append(instruction & 0xFF)
        for d in parameters:
            frame.append(d)
        frame.append(self.checksum(frame[2:]))
        self.uart.write(frame)

    def readframe(self):
        id = 0x00
        instruction = 0x00
        parameters = b''
        frame = self.uart.read()
        if frame is not None:
            frame = bytearray(frame)
            framecpy = frame
            # poor mans frame finding (in case we have some spurious data in front of it)
            while(len(frame) >= 2 and frame[0:2] != b'\xff\xff'):
                frame.pop(0)
            if len(frame) >= 2 and frame[0:2] == b'\xff\xff':
                if len(frame) >= 6:
                    id = frame[2]
                    length = frame[3]
                    instruction = frame[4]
                    if len(frame) >= length + 4: # Data length + header + checksum + length field
                        paramlen = length - 2
                        parameters = frame[5:5+paramlen]
                        cs = frame[5+paramlen]
                        cscal = self.checksum(frame[2:(2 + length + 1)])
                        if cs == cscal:
                            # Checksum matches, return data
                            return (id, instruction, parameters)
                        else:
                            raise FrameException(f"Checksum '{hex(cs)}' in frame does not match calculated checksum '{hex(cscal)}'", frame)    
                    else:
                        raise FrameException("Data length does not match specified length", frame)
                else:
                    raise FrameException("Data is not long enough for a complete frame", frame)    
            else:
                raise FrameException("Frame not detected in read data", framecpy)
        else:
            raise FrameException("No data read from uart", None, True)


''' 
TEST CODE:

from serialservo import ST3215 
from machine import UART, Pin
import time

uart1 = UART(1, baudrate=1000000, tx=Pin(4), rx=Pin(5))
servo = ST3215(uart1)
servo.Ping(1)
location = servo.ReadRegister(1, servo.CURRENT_LOCATION)
print(f"Current Position: {location}");
servo.WriteRegister(1, servo.OPERATION_SPEED, 3400)
target = location  + 20000
servo.WriteRegister(1, servo.TARGET_LOCATION, target)
time.sleep_ms(2000)
servo.WriteRegister(1, servo.OPERATION_SPEED, 100)
target = location
servo.WriteRegister(1, servo.TARGET_LOCATION, target)

cl = 65536
while target != cl:
    cl = servo.ReadRegister(1, servo.CURRENT_LOCATION)
    cc = servo.ReadRegister(1, servo.CURRENT_CURRENT) * 6.5
    print(f"Location: {cl}, Current: {cc} mA")
    time.sleep_ms(500)

''' 