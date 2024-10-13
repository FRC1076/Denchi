# manages I/O with devices for batcon

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

import struct
import io
from abc import ABC, abstractmethod
import tomli

with open("batconfig.toml",'rb') as confile:
    config = tomli.load(confile)

# Base IO class for all MCP3xxx devices
# For simplicity, the SPI device and cd are wrapped in an MCP3xxx class. The code could be made significantly more performant if the SPI device is called directly and the IO class directly read from its output stream
class mcp3xxxIOBase(ABC,io.RawIOBase):
    def __init__(self,adc : MCP.MCP3xxx, pin : int):
        self.adc = adc
        self.pin = pin
    
    # Override
    def writable():
        return False
    
    # Override
    def readable():
        return True
    
    # Override
    def seekable(self):
        return False
    
    # Override
    def seek(self):
        raise IOError("mcp3xxxIO does not support random-access")
    
    # Override
    def tell(self):
        raise IOError("mcp3xxxIO does not support random-access")
    
    # Override
    def truncate(self):
        raise IOError("mcp3xxxIO does not support random-access")
    
    # Override
    def write(self):
        raise IOError("mcp3xxxIO is read-only")
    
    # Override
    def isatty(self):
        return False
    
    # Override
    def fileno(self):
        raise IOError("mcp3xxxIO does not use a file descriptor")
    
    # Override
    @abstractmethod
    def read(self,n=-1):
        raise NotImplementedError
    
    # Override
    @abstractmethod
    def readall(self):
        raise NotImplementedError
    
    # Override
    @abstractmethod
    def readinto(self, buffer):
        raise NotImplementedError
    
    # Override
    def readline(self, size = -1):
        raise IOError("mcp3xxxIO does not support readline")
    
    # Override
    def readlines(self, hint = -1):
        raise IOError("mcp3xxxIO does not support readlines")


class mcp3008IO(mcp3xxxIOBase):

    def __init__(self, adc : MCP.MCP3008, pin : int, readDiff : bool = False):
        super().__init__(adc,pin)
        self.readDiff = readDiff

    def processReading(self, reading : int):
        '''processes raw readings, outputs voltage value in millivolts'''
        return int((reading * config['electrical']['refVoltage']/1024) * 1000 * config['electrical']['voltDivider'])
    
    # Override
    def read(self,size = -1):
        if size == -1:
            return struct.pack(">H",self.processReading(self.adc.read(self.pin,self.readDiff)))
        else:
            return struct.pack(">H",self.processReading(self.adc.read(self.pin,self.readDiff))).rjust(size,'\00')
    
    # Override
    def readall(self):
        return struct.pack(">H",self.processReading(self.adc.read(self.pin,self.readDiff)))
    
    # Override
    def readinto(self, buffer):
        byteBuff = struct.pack(">H",self.processReading(self.adc.read(self.pin,self.readDiff)))
        for i in range(len(byteBuff)):
            buffer[i] = byteBuff[i]
        return len(byteBuff)

    
    




    

    

    

        