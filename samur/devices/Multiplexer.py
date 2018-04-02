import RPi.GPIO as GPIO
from time import sleep

nop = lambda *a, **k: None

class Multiplexer:
    multiplexer_type = '74HC4067'

    def __init__(self, S0Pin, S1Pin, S2Pin, S3Pin, INPin):
        self.S0Pin = S0Pin
        self.S1Pin = S1Pin
        self.S2Pin = S2Pin
        self.S3Pin = S3Pin
        self.INPin = INPin

        GPIO.setup(self.S0Pin, GPIO.OUT)
        GPIO.setup(self.S1Pin, GPIO.OUT)
        GPIO.setup(self.S2Pin, GPIO.OUT)
        GPIO.setup(self.S3Pin, GPIO.OUT)
        GPIO.setup(self.INPin, GPIO.IN)

        GPIO.output(self.S0Pin, GPIO.LOW)
        GPIO.output(self.S1Pin, GPIO.LOW)
        GPIO.output(self.S2Pin, GPIO.LOW)
        GPIO.output(self.S3Pin, GPIO.LOW)

        self.inputs = [GPIO.LOW] * 16

    def read(self):
        for muxPin in range(16):
            GPIO.output(self.S0Pin, (((muxPin) >> (0)) & 0x01))
            GPIO.output(self.S1Pin, (((muxPin) >> (1)) & 0x01))
            GPIO.output(self.S2Pin, (((muxPin) >> (2)) & 0x01))
            GPIO.output(self.S3Pin, (((muxPin) >> (3)) & 0x01))

            # Wait some delay for pins are stable
            nop()

            self.inputs[muxPin] = GPIO.input(self.INPin)

        return self.inputs

