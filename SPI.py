import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)

from gpiozero import PWMLED, MCP3008
from time import sleep
pot = MCP3008(0)
led = PWMLED(14)
while True:
    if (pot.value < 0.001):
        led.value

    else:
        led.value = pot.value
    print(pot.value)
    sleep(0.1)
    