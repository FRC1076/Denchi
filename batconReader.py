from dataclasses import dataclass
import time
import argparse

@dataclass
class batteryTest:
    fingerprint : int
    teamID : str
    batteryID : str
    loadOhms : float
    pollTime : int
    timeStart : time.struct_time
    readings : list[tuple[float,float,int]]
    batteryLife : float
    minvolts : float
    logvolts : float

    def getTimestamp(self):
        '''returns start timestamp as a string'''
        return time.strftime(f"%a %b %d %H:%M:%S%z %Y",self.timeStart)
    def __str__(self):
        outStr = f'------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hex(self.fingerprint)[2:]}\n# Team Number: {self.teamID}\n# Battery ID: {self.batteryID}\n# Load (Ohms): {str(self.loadOhms)}\n# Start Time: {self.getTimestamp()}\n# Poll Interval: {str(self.pollTime)}\n# Delta-V Logging Threshold: {str(self.logvolts)}\n# Minimum Volts: {self.minvolts}\n# Battery Life (Ampere-Hours): {str(self.batteryLife)}\nVoltage (Volts),Current (Amps),Time (ms)\n'
        for reading in self.readings:
            outStr += f'{str(reading[0])},{str(reading[1])},{str(reading[2])}\n'
        return outStr
    
def readlog(filepath : str):
    with open(filepath,'rb') as f:
        logbytes = f.read()
        fingerprint = int.from_bytes(logbytes[0:4],'big',signed=False)
        team = str(int.from_bytes(logbytes[4:6],'big',signed=False))
        batID = logbytes[6:16].decode("ascii").strip('\00')
        startTime = time.localtime(int.from_bytes(logbytes[16:24],'big',signed=False))
        loadohms = int.from_bytes(logbytes[24:28],'big',signed=False)/1000
        polltime = int.from_bytes(logbytes[28:32],'big',signed=False)
        minvolts = int.from_bytes(logbytes[32:36],'big',signed=False)/1000
        logvolts = int.from_bytes(logbytes[36:40],'big',signed=False)/1000
        batteryLife = int.from_bytes(logbytes[40:48],'big',signed=False)/3600
        pointer = 48
        readings = []
        while pointer < len(logbytes):
            reading = (int.from_bytes(logbytes[pointer:pointer+4],'big',signed=False)/1000,
                       int.from_bytes(logbytes[pointer+4:pointer+8],'big',signed=False)/1000,
                       int.from_bytes(logbytes[pointer+8:pointer+12],'big',signed=False))
            readings.append(reading)
            pointer += 12
        return batteryTest(
            fingerprint,
            team,
            batID,
            loadohms,
            polltime,
            startTime,
            readings,
            batteryLife,
            minvolts,
            logvolts
        )



if __name__ == '__main__':
    log = readlog('./logs/fade7cb8_SIMBAT_241012-123747.bclog')
    print(log)
    



