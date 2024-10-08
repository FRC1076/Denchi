import argparse
import time
import sys
import datetime
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
parser.add_argument('--loadohms', type=str,
                    help= 'LoadOhms')
parser.add_argument('--outfile', type=str,
                    help= 'OutputFile', nargs='?', const='history.dat', default='history.dat')

#args.log.write('%s' % (args.id, args.team, args.loadohms, args.outfile))
#args.log.close()

args = parser.parse_args()

file = open(args.outfile, 'a') 
file.write("------------------------------------------------\n")
file.write("# batcon Battery Conditioner and Capacity Test")
file.write(f"\n# TeamID: {args.team} \n# BatteryID: {args.id} \n# LoadOhms: {args.loadohms} \n# StartTime: {str(datetime.datetime.now())}\n")
'''
for i in range(0, 30):
    file.write("# batcon Battery Conditioner and Capacity Test")
    file.write(f"\n# TeamID: {args.team} \n# BatteryID: {args.id} \n# LoadOhms: {args.loadohms} \n# StartTime: {str(datetime.datetime.now())}")
    #a = "\nbattery info"+str(i)
    #file.write(a)
    #time.sleep(0.4)
    """
    file.write(args.id)
    file.write("\n#")
    file.write(args.team)
    file.write("\n#")
    file.write(args.loadohms)
    file.write("\n#")
    file.write(args.outfile)
    """
'''
file.close()