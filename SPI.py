import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from batconio import MCP3008IO
from batlogger import funcStreamBatLogger
from adafruit_mcp3xxx.analog_in import AnalogIn
import tomli

with open("batconfig.toml",'rb') as confile:
    config = tomli.load(confile)

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
mcpIO = MCP3008IO(mcp,config['electrical']['refVoltageRaw'] / config['electrical']['voltScalar'])
print(mcpIO.getPin0_mV())
print(mcpIO.getPin1_mV())
print(mcpIO.getPin2_mV())
print(mcpIO.getPin3_mV())
print(mcpIO.getPin4_mV())
print(mcpIO.getPin5_mV())
print(mcpIO.getPin6_mV())
print(mcpIO.getPin7_mV())

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
    