import argparse
import time
import testADC as ADC
import hashlib
import scipy.integrate as integrate
import os
import tomli
import io
from batlogger import streamBatLogger
from batlogger import funcStreamBatLogger
from batlogger import header
import struct

parser = argparse.ArgumentParser(
    description='criteria for battery conditioner file')

#$ python batconcap.py --id '2025A' --team 1076 --loadohms 6.1 --outfile history.dat $ cat history.dat 
# batconcap Battery Conditioner and Capacity Test 
# TeamID: 1076 
# BatteryID: 2025A 
# LoadOhms: 6.1
# StartTime: Sat Sep 28 12:00:12 EDT 2024 $ 
'''
parser = argparse.ArgumentParser(
    description='sum the integers at the command line')
parser.add_argument(
    'integers', metavar='int', nargs='+', type=int,
    help='an integer to be summed')
parser.add_argument(
    '--log', default=sys.stdout, type=argparse.FileType('w'),
    help='the file where the sum should be written')
args = parser.parse_args()
args.log.write('%s' % sum(args.integers))
args.log.close()
'''
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
    description="batcon Battery Conditioner and Capacity Test"
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

#args.log.write('%s' % (args.id, args.team, args.loadohms, args.outfile))
#args.log.close()
#format for comma-separated values: (Voltage,Current,Time)
if __name__ == "__main__":
    #TODO: Encapsulate argument parser into class
    batSim = ADC.fake1MPC3008(10000,12000,1)
    batSim2 = ADC.fake2MPC3008(
        12000,
        10000,
        10
    )
    args = parser.parse_args()
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
    print(f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {args.team}\n# Battery ID: {args.id}\n# Load (Ohms): {str(args.loadohms)}\n# Start Time: {timestampstr}\n# Poll Interval: {str(args.polltime)}\n# Delta-V Logging Threshold: {str(args.logvolts)}\n# Minimum Volts: {args.minvolts}\n# Logged at: {binfileName}")
    with open(args.outfile, 'a') as outfile:
        outfile.write(f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {args.team}\n# Battery ID: {args.id}\n# Load (Ohms): {str(args.loadohms)}\n# Start Time: {timestampstr}\n# Poll Interval: {str(args.polltime)}\n# Delta-V Logging Threshold: {str(args.logvolts)}\n# Minimum Volts: {args.minvolts}\n# Logged at: {binfileName}\n")
    if not os.path.exists(f"./{config['system']['logdir']}"):
        os.mkdir(f"./{config['system']['logdir']}")
    logfile = open(binfileName,'wb')
    battery = io.BytesIO(int.to_bytes(12000,4,'big')+int.to_bytes(11500,4,'big')+int.to_bytes(11000,4,'big')+int.to_bytes(10500,4,'big')+int.to_bytes(10000,4,'big'))
    batLogger = streamBatLogger(header=header(
            int.from_bytes(hasher.digest(4),'big'),
            args.team,
            args.id,
            args.loadohms,
            args.polltime,
            initialTimestamp,
            int(args.minvolts * 1000),
            int(args.logvolts * 1000)
        ),
        input=battery,
        output=logfile
    )
    batLogger2 = funcStreamBatLogger(header=header(
            int.from_bytes(hasher.digest(4),'big'),
            args.team,
            args.id,
            args.loadohms,
            args.polltime,
            initialTimestamp,
            int(args.minvolts * 1000),
            int(args.logvolts * 1000)
        ),
        input = lambda : next(batSim2),
        output = logfile
    )  
    voltage = int(args.minvolts * 1000) + 1
    batLogger2.start()
    while voltage > (args.minvolts * 1000):
        try:
            voltage = batLogger2.recordReading()[0]
            time.sleep(args.polltime/1000)
        except StopIteration:
            break

    batlife = batLogger2.end()/3600
    logfile.close()
    battery.close()
    with open(args.outfile,'a') as f:
        f.write(f'# Battery Life (Amp-Hours): {batlife}\n')



