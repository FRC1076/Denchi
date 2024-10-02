import argparse
parser = argparse.ArgumentParser()

#$ python batconcap.py --id '2025A' --team 1076 --loadohms 6.1 --outfile history.dat $ cat history.dat 
# batconcap Battery Conditioner and Capacity Test 
# TeamID: 1076 
# BatteryID: 2025A 
# LoadOhms: 6.1
# StartTime: Sat Sep 28 12:00:12 EDT 2024 $ 

parser.add_argument('--id', type=str,
                    help= 'BatteryID')
parser.add_argument('--team', type=int,
                    help= 'TeamID')
parser.add_argument('--loadohms', type=float,
                    help= 'LoadOhms')
parser.add_argument('--outfile', type=str,
                    help= 'StartTime')

print(parser.parse_args())