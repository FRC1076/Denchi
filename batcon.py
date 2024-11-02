import argparse
import tomli
from batconio import MCP3008IO
from batlogger import funcStreamBatLogger
from batlogger import header
import time
import os
import hashlib
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from io import BytesIO, BufferedWriter
from testADC import fake1MPC3008

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

with open("batconfig.toml",'rb') as confile:
    config = tomli.load(confile)

parser = argparse.ArgumentParser(
    description="Battery Conditioner and Capacity Test"
)
parser.add_argument('id', type=str,help= 'ID of the Battery being conditioned')
parser.add_argument('-m','--minvolts', type=float,
                    help='minimum voltage (when the battery reaches this voltage, the battery is considered drained and batcon will stop)',default=config['battery']['minvolts'])
parser.add_argument('-l','--loadohms', type=float,
                    help= 'Resistance load applied to the battery',default=config['battery']['loadohms'])
parser.add_argument('-v','--logvolts', type=float,
                    help="minimum change in voltage needed to be logged (if set to 0, all readings are logged)", default=config['system']['logvolts'])
parser.add_argument('-t','--team', type=str,
                    help= 'Team number',default=config['user']['team'])
parser.add_argument('-o','--outfile', type=str,
                    help= 'File to output text to', default=config['system']['outfile'])
parser.add_argument('-p','--polltime', type=int,
                    help='Polling interval in milliseconds', default=config['system']['polltime'])


class batconFactory():
    '''takes arguments, and generates an MCPIO object, and a batlogger object'''
    def __init__(self,
    id : str,
    loadohms : float,
    minvolts : float,
    logvolts :float,
    team :str,
    polltime : int,
    outfile = "history.dat"
    ) -> None:
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        self.cs = digitalio.DigitalInOut(board.D5)
        self.mcp = MCP.MCP3008(spi,cs)
        self.mcpIO = MCP3008IO(mcp,config['electrical']['refVoltageRaw'] / config['electrical']['voltScalar'])
        if not id:
            raise RuntimeError("no battery ID specified")
        elif not loadohms:
            raise RuntimeError("no resistance load specified")
        elif len(id) > 10:
            raise RuntimeError("Battery ID cannot be longer than 10 characters")
        initialTimestamp = time.localtime(time.time())
        timestampstr = time.strftime(f"%a %b %d %H:%M:%S%z %Y",initialTimestamp)
        hashSeedString = str(team)+str(id)+str(loadohms)+str(polltime)+timestampstr
        hashSeedBytes = bytearray()
        hashSeedBytes.extend(map(ord, hashSeedString))
        hasher = hashlib.shake_256(hashSeedBytes)

        self.binfileName = f"./{config['system']['logdir']}/{hasher.hexdigest(4)}_{id}_{time.strftime(f'%y%m%d-%H%M%S',initialTimestamp)}.bclog"

        self.outfilepath = outfile
        self.headerstring = f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {team}\n# Battery ID: {id}\n# Load (Ohms): {str(loadohms)}\n# Start Time: {timestampstr}\n# Poll Interval: {str(polltime)}\n# Delta-V Logging Threshold: {str(logvolts)}\n# Minimum Volts: {minvolts}\n# Logged at: {self.binfileName}\n"

        self.header = header(
            int.from_bytes(hasher.digest(4),'big'),
            team,
            id,
            loadohms,
            polltime,
            initialTimestamp,
            int(minvolts * 1000),
            int(logvolts * 1000)
        )
    
    def writeHeader(self) -> None:
        with open(self.outfilepath,'a') as f:
            f.write(self.headerstring)
    
    
    def getBatteryIO(self) -> MCP3008IO:
        '''returns the battery IO object'''
        return self.mcpIO

    def getOutputFile(self):
        '''returns a bytestream representing the default output file'''
        return open(self.binfileName,'wb')

    def getFSBatlogger(self, outputstream : BytesIO) -> funcStreamBatLogger:
        '''takes a BytesIO object as an output stream, returns a funcStreamBatLogger configured to log this battery'''
        batLogger = funcStreamBatLogger(
            header=self.header,
            input = self.mcpIO.getPin0_mV,
            output = outputstream
        )
        return batLogger
        
class fakeBatconFactory():
    def __init__(self,
    id : str,
    loadohms : float,
    minvolts : float,
    logvolts :float,
    team :str,
    polltime : int,
    outfile="history.dat"
    ) -> None:
        self.batsim = fake1MPC3008(10000,12000,5)
        if not id:
            raise RuntimeError("no battery ID specified")
        elif not loadohms:
            raise RuntimeError("no resistance load specified")
        elif len(id) > 10:
            raise RuntimeError("Battery ID cannot be longer than 10 characters")
        initialTimestamp = time.localtime(time.time())
        timestampstr = time.strftime(f"%a %b %d %H:%M:%S%z %Y",initialTimestamp)
        hashSeedString = str(team)+str(id)+str(loadohms)+str(polltime)+timestampstr
        hashSeedBytes = bytearray()
        hashSeedBytes.extend(map(ord, hashSeedString))
        hasher = hashlib.shake_256(hashSeedBytes)
        self.binfileName = f"./{config['system']['logdir']}/{hasher.hexdigest(4)}_{id}_{time.strftime(f'%y%m%d-%H%M%S',initialTimestamp)}.bclog"
        
        self.outfilepath = outfile
        self.headerstring = f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {team}\n# Battery ID: {id}\n# Load (Ohms): {str(loadohms)}\n# Start Time: {timestampstr}\n# Poll Interval: {str(polltime)}\n# Delta-V Logging Threshold: {str(logvolts)}\n# Minimum Volts: {minvolts}\n# Logged at: {self.binfileName}\n"

        self.header = header(
            int.from_bytes(hasher.digest(4),'big'),
            team,
            id,
            loadohms,
            polltime,
            initialTimestamp,
            int(minvolts * 1000),
            int(logvolts * 1000)
        )

    def writeHeader(self) -> None:
        with open(self.outfilepath,'a') as f:
            f.write(self.headerstring)
    
    def getFakeBatteryIO(self) -> fake1MPC3008:
        '''returns the battery IO object'''
        return self.batsim

    def getOutputFile(self) -> BufferedWriter:
        '''returns a bytestream representing the default output file'''
        return open(self.binfileName,'wb')

    def getFSBatlogger(self, outputstream : BytesIO) -> funcStreamBatLogger:
        '''takes a BytesIO object as an output stream, returns a funcStreamBatLogger configured to log this battery'''
        batLogger = funcStreamBatLogger(
            header=self.header,
            input = self.batsim.voltage,
            output = outputstream
        )
        return batLogger

if __name__ == "__main__":

    args = parser.parse_args()

    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(board.D5)
    mcp = MCP.MCP3008(spi, cs)
    mcpIO = MCP3008IO(mcp,config['electrical']['refVoltageRaw'] / config['electrical']['voltScalar'])

    if not args.id:
        raise RuntimeError("no battery ID specified")
    elif not args.loadohms:
        raise RuntimeError("no resistance load specified")
    elif len(args.id) > 10:
        raise RuntimeError("Battery ID cannot be longer than 10 characters")
    initialTimestamp = time.localtime(time.time())
    timestampstr = time.strftime(f"%a %b %d %H:%M:%S%z %Y",initialTimestamp)
    hashSeedString = str(args.team)+str(args.id)+str(args.loadohms)+str(args.polltime)+timestampstr
    hashSeedBytes = bytearray()
    hashSeedBytes.extend(map(ord, hashSeedString))
    hasher = hashlib.shake_256(hashSeedBytes)
    binfileName = f"./{config['system']['logdir']}/{hasher.hexdigest(4)}_{args.id}_{time.strftime(f'%y%m%d-%H%M%S',initialTimestamp)}.bclog"
    #binfileName = f"./{config['system']['logdir']}/{hasher.hexdigest(4)}-{args.id}.bclog"
    print(f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {args.team}\n# Battery ID: {args.id}\n# Load (Ohms): {str(args.loadohms)}\n# Start Time: {timestampstr}\n# Poll Interval: {str(args.polltime)}\n# Delta-V Logging Threshold: {str(args.logvolts)}\n# Minimum Volts: {args.minvolts}\n# Logged at: {binfileName}\nVoltage V,Current A,Time ms")
    with open(args.outfile, 'a') as outfile:
        outfile.write(f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {args.team}\n# Battery ID: {args.id}\n# Load (Ohms): {str(args.loadohms)}\n# Start Time: {timestampstr}\n# Poll Interval: {str(args.polltime)}\n# Delta-V Logging Threshold: {str(args.logvolts)}\n# Minimum Volts: {args.minvolts}\n# Logged at: {binfileName}\n")
    if not os.path.exists(f"./{config['system']['logdir']}"):
        os.mkdir(f"./{config['system']['logdir']}")
    logfile = open(binfileName,'wb')
    voltage_V = 100000000000000000000000000000000000000000
    batLogger = funcStreamBatLogger(header=header(
            int.from_bytes(hasher.digest(4),'big'),
            args.team,
            args.id,
            args.loadohms,
            args.polltime,
            initialTimestamp,
            int(args.minvolts * 1000),
            int(args.logvolts * 1000)
        ),
        input = mcpIO.getPin0_mV,
        output = logfile
    )
    batLogger.start() 
    while voltage_V > args.minvolts:
        reading = batLogger.recordReading() #(voltage_mV,current_mA,time_ms)
        voltage_V = reading[0]/1000
        current_A = reading[1]/1000
        time_ms = reading[2]
        print(f"{voltage_V},{current_A},{time_ms}")
        time.sleep(args.polltime/1000)
    batlife = batLogger.end()/3600
    logfile.close()
    print(f"# Battery Life (Amp-Hours): {batlife}")
    with open(args.outfile,'a') as f:
        f.write(f'# Battery Life (Amp-Hours): {batlife}\n')





