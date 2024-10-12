import argparse
import time
import testADC as ADC
import hashlib
import scipy.integrate as integrate
import os
import tomli

#NOTE: Binary mode stores headers for Linux
battery = ADC.fake0MPC3008([12000,11500,11000,10500,10000])
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
parser.add_argument('-i','--id', type=str,
                    help= 'ID of the Battery being conditioned')
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
args = parser.parse_args()
if not args.id:
    raise RuntimeError("no battery ID specified")
elif not args.loadohms:
    raise RuntimeError("no resistance load specified")
elif len(args.id) > 10:
    raise RuntimeError("Battery ID cannot be longer than 10 characters")
initialTimestamp = time.localtime(time.time())
initProcessTime = time.perf_counter_ns() // 1000000 #Process time in milliseconds
timestamp = time.strftime(f"%a %b %d %H:%M:%S%z %Y",initialTimestamp)
hashSeedString = str(args.team)+str(args.id)+str(args.loadohms)+str(args.polltime)+timestamp
hashSeedBytes = bytearray()
hashSeedBytes.extend(map(ord, hashSeedString))
hasher = hashlib.shake_256(hashSeedBytes)
binfileName = f"./{config['system']['logdir']}/{hasher.hexdigest(4)}_{args.id}_{initialTimestamp.strftime(f'%y%m%d-%H%M%S')}.bclog"
#binfileName = f"./{config['system']['logdir']}/{hasher.hexdigest(4)}-{args.id}.bclog"
print("batcon Battery Conditioner and Capacity Test")
print(f"Fingerprint: {hasher.hexdigest(4)}\nTeamID: {args.team}\nBatteryID: {args.id}\nLoadOhms: {str(args.loadohms)}\nStartTime: {timestamp}\nPollTime: {str(args.polltime)}\n")


currentReadings = [] #list of current readings (amperes)
timedeltas = [] #list of time deltas where readings were taken (seconds)
logs = []
voltage = (args.minvolts * 1000) + 1
lastLoggedVoltage = 1000000000
while voltage > (args.minvolts * 1000):
    #TODO: Optimize, remove datetime stuff and unnecessary unit conversions, fix batcon reader
    processTime = (time.perf_counter_ns()//1000000) - initProcessTime #processTime in milliseconds
    voltage = battery.voltage() #voltage in milliamps
    current = int(voltage/args.loadohms) #current in milliamps
    if (lastLoggedVoltage - voltage) >= (args.logvolts*1000):
        logs.append((voltage,current,processTime))
        current /= 1000 #current in amps
        currentReadings.append(current)
        timedeltas.append(processTime/1000)
    time.sleep(args.polltime/1000)

ampereSeconds = int(integrate.simpson(
    y = currentReadings,
    x = timedeltas
)) # Gives result in ampere-seconds. Results are cast to int, so if the result is below 1, ampereseconds will equal zero
with open(args.outfile, 'a') as outfile:
    outfile.write(f"------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hasher.hexdigest(4)}\n# Team Number: {args.team}\n# Battery ID: {args.id}\n# Load (Ohms): {str(args.loadohms)}\n# Start Time: {timestamp}\n# Poll Interval: {str(args.polltime)}\n# Delta-V Logging Threshold: {str(args.logvolts)}\n# Minimum Volts: {args.minvolts}\n# Battery Life (Ampere-Hours): {str(ampereSeconds/3600)}\n# Logged at: {binfileName}\n")

if not os.path.exists(f"./{config['system']['logdir']}"):
    os.mkdir(f"./{config['system']['logdir']}")

with open(binfileName,'wb') as binlog:
    binlog.write(hasher.digest(4))
    binlog.write(bytes(intToBytes(int(args.team),size=16)))
    binlog.write(bytes(args.id.rjust(10,'\00'),'ascii'))
    binlog.write(bytes(intToBytes(int(time.mktime(initialTimestamp)),size=64)))
    binlog.write(bytes(intToBytes(int(args.loadohms*1000),size=32)))
    binlog.write(bytes(intToBytes(int(args.polltime),size=32)))
    binlog.write(bytes(intToBytes(int(args.minvolts*1000),size=32)))
    binlog.write(bytes(intToBytes(int(args.logvolts*1000),size=32)))
    binlog.write(bytes(intToBytes(ampereSeconds,size=64)))
    for log in logs:
        binlog.write(bytes(intToBytes(log[0],size=32)))
        binlog.write(bytes(intToBytes(log[1],size=32)))
        binlog.write(bytes(intToBytes(log[2],size=32)))


