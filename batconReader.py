from dataclasses import dataclass
from datetime import datetime
import re
import csv

@dataclass
class batteryTest:
    hashID : str
    teamID : str
    batteryID : str
    loadOhms : float
    pollTime : int
    pollNum : int
    timeStart : datetime
    readings : list[tuple[float,float,datetime]]

class batconReader:
    headerRegex = re.compile(r'# batcon Battery Conditioner and Capacity Test\n# TeamID: (.+)\n# BatteryID: (.+)\n# LoadOhms: (.+)\n# StartTime: (.+)\n# PollTime: (.+)\n# PollNum: (.+)\n# HashID: (.+)')
    def __init__(self,filepath=None):
        self.filepath = filepath
        self.tests = {}

    def setFilepath(self,filepath):
        self.filepath = filepath

    def parseFile(self):
        f = open(self.filepath,'r')
        fileText = f.read()
        entryList = fileText.split('------------------------------------------------\n')
        for entry in entryList:
            header = self.headerRegex.match(entry)
            if header:
                teamid = header.group(1)
                batid = header.group(2)
                loadohms = float(header.group(3))
                starttime = datetime.strptime(header.group(4), '%Y-%m-%d %H:%M:%S.%f%z')
                polltime = int(header.group(5))
                pollnum = int(header.group(6))
                hashid = header.group(7)
                readings = entry.split('Voltage,Current,Timestamp\n')[1]
                readings = readings.split('\n')[:-1]
                readings = csv.reader(readings)
                processedReadings = [(float(reading[0]),float(reading[1]),datetime.strptime(reading[2], '%H:%M:%S.%f')) for reading in readings]
                self.tests[hashid] = batteryTest(hashid,teamid,batid,loadohms,polltime,pollnum,starttime,processedReadings)
    
if __name__ == '__main__':
    reader = batconReader('history.dat')
    reader.parseFile()
    for ele in reader.tests.values():
        print(ele.hashID)
    



