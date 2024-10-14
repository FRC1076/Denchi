
import time
from dataclasses import dataclass
from abc import ABCMeta, abstractmethod
from typing import BinaryIO
from scipy import integrate
import sys

def intToBytes(num,size=32):
    #Converts ints into bytes
    #size is in bits, not bytes
    if num < 0:
        num += (1 << size) 
    bytes = []
    for i in range(size//8):
        byte = (num % (1 << size-(8*i))) >> (size - 8 * (i+1))
        bytes.append(byte)
    return tuple(bytes)

@dataclass
class header:
    fingerprint : int
    teamID : str
    batteryID : str
    loadOhms : float
    pollTime : int
    timeStart : time.struct_time
    minvolts : int #millivolts
    logvolts : int #millivolts

class batLoggerBase(metaclass=ABCMeta):

    def __init__(self,header:header):
        self.header = header
    
    def __str__(self):
        return f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hex(self.header.fingerprint)[2:]}\n# Team Number: {self.header.teamID}\n# Battery ID: {self.header.batteryID}\n# Load (Ohms): {str(self.header.loadOhms)}\n# Start Time: {self.header.getTimestamp()}\n# Poll Interval: {str(self.header.pollTime)}\n# Delta-V Logging Threshold: {str(self.header.logvolts)}\n# Minimum Volts: {self.header.minvolts}\n"
    
    @abstractmethod
    def recordReading(self, voltage: int, current: int, time: int):
        '''
        Voltage in millivolts
        Current in milliamps
        Time in milliseconds since start of testing
        '''
        raise NotImplementedError

    @abstractmethod
    def end(self):
        '''
        end the logging, write ending to output
        '''
        raise NotImplementedError

    @abstractmethod
    def start(self):
        '''
        begin the logging, write header to output
        '''
        raise NotImplementedError

class streamBatLogger(batLoggerBase):

    '''
    receives data from an input bytes-like object, logs data to an output bytes-like object
    '''
    def __init__(self,header,input:BinaryIO,output:BinaryIO):
        super().__init__(header)
        self.instream = input
        self.outstream = output
        self.logs = []
        self.startTimeInternal = None #internal timer, separate from the header's timestamp. time is measured in milliseconds
        self.previousVoltage = 100000000000000000 #For measuring voltage difference
    
    def start(self):
        self.startTimeInternal = time.perf_counter_ns()//1000000
        self.outstream.write(bytes(intToBytes(self.header.fingerprint,size=32)))
        self.outstream.write(bytes(intToBytes(int(self.header.teamID),size=16)))
        self.outstream.write(bytes(self.header.batteryID.rjust(10,'\00'),'ascii'))
        self.outstream.write(bytes(intToBytes(int(time.mktime(self.header.timeStart)),size=64)))
        self.outstream.write(bytes(intToBytes(int(self.header.loadOhms*1000),size=32)))
        self.outstream.write(bytes(intToBytes(int(self.header.pollTime),size=32)))
        self.outstream.write(bytes(intToBytes(int(self.header.minvolts),size=32)))
        self.outstream.write(bytes(intToBytes(int(self.header.logvolts),size=32)))

    def end(self):
        '''ends logging, returns battery life calculation'''
        currentReadings = [ele[1]/1000 for ele in self.logs] #current readings in amperes
        deltaS = [ele[2]/1000 for ele in self.logs] #timestamps in seconds
        ampereSeconds = int(integrate.simpson(
            y = currentReadings,
            x = deltaS
        ))
        self.outstream.write(bytes(intToBytes(ampereSeconds,size=64)))
        self.outstream.close()
        return ampereSeconds

    def recordReading(self):
        '''
        automatically records a reading from the input stream and records it to the output stream if the voltage difference is high enough. Also returns a copy of the voltage reading
        '''
        voltage_mV = int.from_bytes(self.instream.read(4),'big')
        current_mA = int(voltage_mV/self.header.loadOhms)
        time_ms = (time.perf_counter_ns()//1000000) - self.startTimeInternal
        if self.previousVoltage - voltage_mV >= self.header.logvolts:
            self.outstream.write(bytes(intToBytes(voltage_mV,size=32)))
            self.outstream.write(bytes(intToBytes(current_mA,size=32)))
            self.outstream.write(bytes(intToBytes(time_ms,size=32)))
            self.logs.append((voltage_mV,current_mA,time_ms))
            self.previousVoltage = voltage_mV
        return voltage_mV

class pipeLogger(streamBatLogger):
    '''receives data from stdin, logs data to stdout. Is meant to be piped in a unix-like system'''
    def __init__(self,header):
        super().__init__(
            header,
            sys.stdin.buffer,
            sys.stdout.buffer
        )
    





