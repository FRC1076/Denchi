from dataclasses import dataclass
import time
import argparse
import os
import pandas

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
        while pointer < len(logbytes)-8:
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
    parser = argparse.ArgumentParser(
        description="Command line tool to process and export .bclog files"
    )
    subparsers = parser.add_subparsers()
    parser.add_argument("logpath",type=str,help="path to log file")
    parser.add_argument("-v","--verbose",action="store_true")

    exportParser = subparsers.add_parser("E",help="export log",aliases=["Export","export"])
    exportParser.set_defaults(export=True)
    
    exportParser.add_argument("-o","--outdir",help="name of the folder to export files to (must include trailing slash)",type=str,default='./')
    exportParser.add_argument("-c","--compress",help="whether the export folder should be compressed",action="store_true")
    exportParser.add_argument("-n","--name",help="Name of the exported files",type=str,default=None,dest="exportname")
    exportParser.add_argument("--csv",help="export logs as a .csv file",action="store_true")
    exportParser.add_argument("--json",help="export logs as a .json file",action="store_true")

    args = parser.parse_args()
    log = readlog(args.logpath)
    if args.verbose:
        print(f"Retrieved {args.logpath} at {time.strftime(f'%a %b %d %H:%M:%S%z %Y',time.localtime())}:")
        print(log)
        print("------------------------------------------------")

    if args.export:
        exportname = f"{hex(log.fingerprint)[2:]}_{log.batteryID}_{time.strftime(f'%y%m%d-%H%M%S',log.timeStart)}"

        if args.exportname is not None:
            exportname = args.exportname

        if args.verbose:
            print(f"Exporting log {hex(log.fingerprint)[2:]} to {args.outdir}{exportname}/")
            print(f"----------------EXPORT SETTINGS-----------------\nCOMPRESSED: {args.compress}\nCSV: {args.csv}\nJSON: {args.json}\n")
        
        exportPath = args.outdir + exportname + '/'
        os.mkdir(exportPath)#TODO: Check if directory already exists

        #generate header file
        with open(exportPath + '/HEADER.txt',"w") as headerf:
            headerf.write(f"# Battery Conditioner and Capacity Test\n# Fingerprint: {hex(log.fingerprint)[2:]}\n# Team Number: {log.teamID}\n# Battery ID: {log.batteryID}\n# Load (Ohms): {str(log.loadOhms)}\n# Start Time: {log.getTimestamp()}\n# Poll Interval: {str(log.pollTime)}\n# Delta-V Logging Threshold: {str(log.logvolts)}\n# Minimum Volts: {log.minvolts}\n# Battery Life (Ampere-Hours): {str(log.batteryLife)}\n")
        
        if args.csv:
            with open(exportPath + '/data.csv') as  csvf:
                pass
            
    



