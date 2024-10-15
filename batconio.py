# manages I/O with devices for batcon

from adafruit_bus_device.spi_device import SPIDevice
import busio
import digitalio
import struct
import io
from collections.abc import ByteString
from abc import ABCMeta, abstractmethod

# To improve readability, any abstract classes should explicitly have their metaclass set to ABCMeta
class SPIDeviceReaderBase(io.RawIOBase,metaclass=ABCMeta):
    def __init__(self,spi : busio.SPI, cs : digitalio.DigitalInOut):
        self._device = SPIDevice(spi,cs)
    
    # Override
    def writable(self) -> bool:
        return False
    
    # Override

    def readable(self) -> bool:
        return True
    
    # Override
    def seekable(self) -> bool:
        return False
    
    # Override
    def seek(self) -> None:
        raise IOError("SPIDeviceReader does not support random-access")
    
    # Override
    def tell(self) -> None:
        raise IOError("SPIDeviceReader does not support random-access")
    
    # Override
    def truncate(self) -> None:
        raise IOError("SPIDeviceReader does not support random-access")
    
    # Override
    def write(self) -> None:
        raise IOError("SPIDeviceReader is read-only")
    
    # Override
    def isatty(self) -> bool:
        return False
    
    # Override
    def fileno(self) -> None:
        raise IOError("SPIDeviceReader does not use a file descriptor")
    
    # Override
    @abstractmethod
    def read(self,n=-1) -> bytes:
        raise NotImplementedError
    
    # Override
    @abstractmethod
    def readall(self) -> bytes:
        raise NotImplementedError
    
    # Override
    @abstractmethod
    def readinto(self, buffer : ByteString) -> int:
        raise NotImplementedError
    
    # Override
    def readline(self, size = -1) -> None:
        raise IOError("SPIDeviceReader does not support readline")
    
    # Override
    def readlines(self, hint = -1) -> None:
        raise IOError("SPIDeviceReader does not support readlines")
    
# Base IO class for all ADC readers
class adcReaderBase(SPIDeviceReaderBase,metaclass=ABCMeta):

    def __init__(self,spi : busio.SPI, cs : digitalio.DigitalInOut,refVolts : float):
        """
        base class for adc reader

        :param SPI spi: SPI
        :param DigitalInOut cs: TODO: Add note
        :param float refVolts: reference voltage, compensated for any scaling (voltage division, etc.) applied to the signal
        """
        super().__init__(spi,cs)
        self.refVolts = refVolts

    @abstractmethod
    def getAnalog_mV(self, reading : int) -> int:
        '''Processes digital reading to be expressed in millivolts'''
        raise NotImplementedError
    
    @abstractmethod
    def getAnalog_V(self, reading : int) -> float:
        '''Processes digital reading to be expressed in volts'''
        raise NotImplementedError

# Base class for all MCP3xxx readers
class mcp3xxxReaderBase(adcReaderBase,metaclass=ABCMeta):
    #TODO: add default refvoltage
    def __init__(self, 
                 spi : busio.SPI, 
                 cs : digitalio.DigitalInOut,
                 pin : int, 
                 refVolts : float, 
                 readDiff : bool = False):
        """
        Base class for all mcp3xxx readers. Reads from a single pin on the mcp3xxx DEPRECATED
    
        :param busio.SPI spi: SPI device
        :param digitalio.DigitalInOut cs: chip select pin
        :param int pin: pin to read from
        :param float refVolts: ADC reference voltage, compensated for any scaling (volt division, etc.) applied to the signal.
        :param bool readDiff: whether or not the device should take a differential reading
        """
        super().__init__(spi,cs,refVolts)
        self._out_buf = bytearray(3)
        self._in_buf = bytearray(3)
        self._pin = pin
        self._readDiff = readDiff
    
    def getPin(self) -> int:
        return self._pin
    
    def setPin(self,pin : int) -> None:
        self._pin = pin
    
    def isDiff(self) -> bool:
        return self._readDiff
    
    def enableDiff(self, diff : bool) -> None:
        self._readDiff = diff

    # Override
    def getAnalog_V(self, reading) -> float:
        return (reading/1024) * self.refVolts
    
    # Override
    def getAnalog_mV(self, reading) -> int:
        return int(self.getAnalog_V(reading) * 1000)
    
    def __read(self, pin: int, is_differential: bool = False) -> int:
        """SPI Interface for MCP3xxx-based ADCs reads. Due to 10-bit accuracy, the returned
        value ranges [0, 1023].

        :param int pin: individual or differential pin.
        :param bool is_differential: single-ended or differential read.
        """
        self._out_buf[1] = ((not is_differential) << 7) | (pin << 4)
        with self._device as spi:
            spi.write_readinto(self._out_buf, self._in_buf)
        return ((self._in_buf[1] & 0x03) << 8) | self._in_buf[2]
    
    # Override
    def readinto(self, buffer : ByteString) -> int:
        byteBuff = struct.pack(">H",self.getAnalog_mV(self.__read(self._pin,self._readDiff)))
        for i in range(len(byteBuff)):
            buffer[i] = byteBuff[i]
        return len(byteBuff)
    
    # Override
    def readall(self) -> bytes:
        return struct.pack(">H",self.getAnalog_mV(self.__read(self._pin,self._readDiff)))
    
    # Override
    def read(self, size = -1) -> bytes:
        '''returns reading, expressed as millivolts, as big-endian bytes in a bytes object of size `size`'''
        if size != -1:
            return struct.pack(">H",self.getAnalog_mV(self.__read(self._pin,self._readDiff))).rjust(size,'\00')
        return self.readall()

class mcp3008Reader(mcp3xxxReaderBase):
    def __init__(
            self, 
            spi : busio.SPI, 
            cs : digitalio.DigitalInOut,
            refVolts : float, 
            pin : int, 
            readDiff : bool = False):
        """
        Class for mcp3008 readers. Reads from a single pin on the mcp3008

        MCP3008 Differential channel mapping. The following list of available differential readings
        takes the form ``(positive_pin, negative_pin) = (channel A) - (channel B)``.

        - (P0, P1) = CH0 - CH1
        - (P1, P0) = CH1 - CH0
        - (P2, P3) = CH2 - CH3
        - (P3, P2) = CH3 - CH2
        - (P4, P5) = CH4 - CH5
        - (P5, P4) = CH5 - CH4
        - (P6, P7) = CH6 - CH7
        - (P7, P6) = CH7 - CH6

        If you are taking differential values, you should enter the pin of the first channel in the mapping
    
        :param busio.SPI spi: SPI device
        :param digitalio.DigitalInOut cs: chip select pin
        :param int pin: pin to read from
        :param float refVolts: ADC reference voltage, compensated for any scaling (volt division, etc.) applied to the signal.
        :param bool readDiff: whether or not the device should take a differential reading
        """
        super().__init__(spi,cs,refVolts,pin,readDiff)
        self._out_buf[0] = 0x01

def ADCIOFuncFactory(dMin,dMax,refVolts,readFunc):
    '''a function factory that generates a function which translates an ADC's digital output into an analog signal in millivolts
    
    :param dMin: The minimum digital value of the ADC 
    :param dMax: The maximum digital value of the ADC
    :param refVolts: The maximum voltage reading of the ADC (adjusted for any signal attenuation)
    :param ADCReadFunc: a function that returns a direct digital reading from the ADC.
    '''
    return lambda *args,**kwargs : (int)((readFunc(*args,**kwargs)/(dMax-dMin) - dMin) * refVolts * 1000)
if __name__ == "__main__":
    print(type(SPIDeviceReaderBase))
    print(type(lambda x : 2))
    MCP3008Function = ADCIOFuncFactory(
        0,
        1023,
        12,
        lambda x : 10 * x
    )
    print(MCP3008Function(100))

    

    

        