import argparse
import time
import datetime
import testADC as ADC
import hashlib
import scipy.integrate as integrate

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
parser.add_argument('--id', type=str,
                    help= 'BatteryID')
parser.add_argument('--team', type=str,
                    help= 'TeamID', nargs='?',const='1076',default='1076')
parser.add_argument('--loadohms', type=float,
                    help= 'LoadOhms')
parser.add_argument('--outfile', type=str,
                    help= 'OutputFile', nargs='?', const='history.dat', default='history.dat')
parser.add_argument('--polltime', type=int,
                    help='Polling interval in milliseconds', nargs='?',const='100',default='100')

#args.log.write('%s' % (args.id, args.team, args.loadohms, args.outfile))
#args.log.close()
#format for comma-separated values: (Voltage,Current,Time)
args = parser.parse_args()
if not args.id:
    raise RuntimeError("no battery ID specified")
elif not args.loadohms:
    raise RuntimeError("no resistance load specified")
initialTimestamp = datetime.datetime.now().astimezone()
timestamp = str(initialTimestamp)
hashSeedString = str(args.team)+str(args.id)+str(args.loadohms)+str(args.polltime)+timestamp
hashSeedBytes = bytearray()
hashSeedBytes.extend(map(ord, hashSeedString))
hasher = hashlib.shake_256(hashSeedBytes)
print("batcon Battery Conditioner and Capacity Test")
print(f"HashID: {hasher.hexdigest(4)}\nTeamID: {args.team}\nBatteryID: {args.id}\nLoadOhms: {str(args.loadohms)}\nStartTime: {timestamp}\nPollTime: {str(args.polltime)}\n")

file = open(args.outfile, 'a') 
file.write("------------------------------------------------\n")
file.write("# batcon Battery Conditioner and Capacity Test")
file.write(f"\n# HashID: {hasher.hexdigest(4)}\n# TeamID: {args.team}\n# BatteryID: {args.id}\n# LoadOhms: {str(args.loadohms)}\n# StartTime: {timestamp}\n# PollTime: {str(args.polltime)}\nVoltage,Current,Timestamp\n")
currentReadings = [] #list of current readings (amperes)
timedeltas = [] #list of time deltas where readings were taken (seconds)

for i in range(5):
    timestamp = datetime.datetime.now().astimezone() #timestamp
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

