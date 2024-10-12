import argparse
import time
import datetime
import testADC as ADC
import hashlib
import scipy.integrate as integrate
import os

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
parser = argparse.ArgumentParser(
    description="batcon Battery Conditioner and Capacity Test"
)
parser.add_argument('-i','--id', type=str,
                    help= 'ID of the Battery being conditioned')
parser.add_argument('-m','--minvolts', type=float,
                    help='minimum voltage (when the battery reaches this voltage, the battery is considered drained and batcon will stop)')
parser.add_argument('-l','--loadohms', type=float,
                    help= 'Resistance load applied to the battery')
parser.add_argument('-s','logvolts', type=float,
                    help="minimum change in voltage needed to be logged (if set to 0, all readings are logged)", default='0.0')
parser.add_argument('-t','--team', type=str,
                    help= 'Team number (defaults to 1076)',default='1076')
parser.add_argument('-o','--outfile', type=str,
                    help= 'File to output text to (defaults to \'history.dat\')', default='history.dat')
parser.add_argument('-p','--polltime', type=int,
                    help='Polling interval in milliseconds (defaults to 100)', default='100')
parser.add_argument('-b','--binary', action='store_true',default=False, nargs=0,
                    help='Whether or not to generate binary logfile (defaults to false)')

#args.log.write('%s' % (args.id, args.team, args.loadohms, args.outfile))
#args.log.close()
#format for comma-separated values: (Voltage,Current,Time)
args = parser.parse_args()
if not args.id:
    raise RuntimeError("no battery ID specified")
elif not args.loadohms:
    raise RuntimeError("no resistance load specified")
initialTimestamp = datetime.datetime.now().astimezone()
initProcessTime = time.process_time_ns() // 1000000 #Process time in milliseconds
timestamp = str(initialTimestamp)
hashSeedString = str(args.team)+str(args.id)+str(args.loadohms)+str(args.polltime)+timestamp
hashSeedBytes = bytearray()
hashSeedBytes.extend(map(ord, hashSeedString))
hasher = hashlib.shake_256(hashSeedBytes)
print("batcon Battery Conditioner and Capacity Test")
print(f"Fingerprint: {hasher.hexdigest(4)}\nTeamID: {args.team}\nBatteryID: {args.id}\nLoadOhms: {str(args.loadohms)}\nStartTime: {timestamp}\nPollTime: {str(args.polltime)}\n")


file = open(args.outfile, 'a') 
file.write("------------------------------------------------\n")
file.write("# batcon Battery Conditioner and Capacity Test")
file.write(f"\n# Fingerprint: {hasher.hexdigest(4)}\n# TeamID: {args.team}\n# BatteryID: {args.id}\n# LoadOhms: {str(args.loadohms)}\n# StartTime: {timestamp}\n# PollTime: {str(args.polltime)}\nVoltage,Current,Timestamp\n")
currentReadings = [] #list of current readings (amperes)
timedeltas = [] #list of time deltas where readings were taken (seconds)
logs = []
for i in range(5):
    #TODO: Optimize, remove datetime stuff and unnecessary unit conversions, fix batcon reader
    timestamp = datetime.datetime.now().astimezone() #timestamp
    processTime = (time.process_time_ns()//1000000) - initProcessTime
    logs.append(voltage,current,processTime)
    voltage = battery.voltage()/1000 #voltage in volts
    current = voltage/args.loadohms #current in amps
    file.write(f'{str(voltage)},{str(current)},{str(timestamp)}\n')
    currentReadings.append(current)
    timedeltas.append((timestamp-initialTimestamp).total_seconds())
    time.sleep(args.polltime/1000)

ampereHours = integrate.simpson(
    y = currentReadings,
    x = timedeltas
) # Gives result in ampere-seconds, not ampere hours. units need to be converted
ampereHours *= 0.0002777778
file.write(f'Battery Life: {str(ampereHours)}\n')
file.close()

if args.binary:
    binfile = 0
    binfileName = f"logs/{hasher.hexdigest(4)}_{args.team}_{args.id}_{initialTimestamp.strftime(f'%y%m%d-%H%M%S')}.bindat"
    try:
        binfile = open(binfileName,'wb')
    except FileNotFoundError:
        print("WARNING: directory './logs' not found")
        os.mkdir('logs')
        print("directory './logs' successfully created")
        binfile = open(binfileName,'wb')
    

