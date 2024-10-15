from dataclasses import dataclass
import time
import argparse
import tarfile
import io
import os
import pandas as pd
import tomli
from typing import BinaryIO

with open("batconfig.toml",'rb') as confile:
    config = tomli.load(confile)

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
    
    def getISO8601Timestamp(self):
        '''returns start timestamp as an ISO-8601 compliant string'''
        return time.strftime(f"%Y-%m-%dT%H:%M:%S%z",self.timeStart)
    def __str__(self):
        outStr = f'------------------------------------------------\n# Battery Conditioner and Capacity Test\n# Fingerprint: {hex(self.fingerprint)[2:]}\n# Team Number: {self.teamID}\n# Battery ID: {self.batteryID}\n# Load (Ohms): {str(self.loadOhms)}\n# Start Time: {self.getTimestamp()}\n# Poll Interval: {str(self.pollTime)}\n# Delta-V Logging Threshold: {str(self.logvolts)}\n# Minimum Volts: {self.minvolts}\n# Battery Life (Ampere-Hours): {str(self.batteryLife)}\nVoltage (Volts),Current (Amps),Time (ms)'
        for reading in self.readings:
            outStr += f'\n{str(reading[0])},{str(reading[1])},{str(reading[2])}'
        return outStr

def readStream(logStream : BinaryIO):
    logbytes = logStream.read()
    fingerprint = int.from_bytes(logbytes[0:4],'big',signed=False)
    team = str(int.from_bytes(logbytes[4:6],'big',signed=False))
    batID = logbytes[6:16].decode("utf-8").strip('\00')
    startTime = time.localtime(int.from_bytes(logbytes[16:24],'big',signed=False))
    loadohms = int.from_bytes(logbytes[24:28],'big',signed=False)/1000
    polltime = int.from_bytes(logbytes[28:32],'big',signed=False)
    minvolts = int.from_bytes(logbytes[32:36],'big',signed=False)/1000
    logvolts = int.from_bytes(logbytes[36:40],'big',signed=False)/1000
    batteryLife = int.from_bytes(logbytes[40:48],'big',signed=False)/3600
    pointer = 40
    readings = []
    while pointer < len(logbytes)-8:
        reading = (int.from_bytes(logbytes[pointer:pointer+4],'big',signed=False)/1000,
                    int.from_bytes(logbytes[pointer+4:pointer+8],'big',signed=False)/1000,
                    int.from_bytes(logbytes[pointer+8:pointer+12],'big',signed=False))
        readings.append(reading)
        pointer += 12
    batteryLife = int.from_bytes(logbytes[pointer:pointer+8],'big',signed=False)/3600
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

def readlog(filepath : str):
    with open(filepath,'rb') as f:
        log = readStream(f)
    return log

def exportLogToTar(log : batteryTest, dest, args, compress=False, verbose = False) -> None:
    '''
    args is a list of filetypes to export to. Options include:
    csv,tsv,xml,arrow,parquet,orc,json'''
    files = {
        'header.json' : bytes(f" {{ \n\t\"fingerprint\": \"{hex(log.fingerprint)}\",\n\t\"team\": \"{log.teamID}\",\n\t\"battery\": \"{log.batteryID}\",\n\t\"loadOhms\": {str(log.loadOhms)},\n\t\"startTime\": \"{log.getISO8601Timestamp()}\",\n\t\"pollTime\": {str(log.pollTime)},\n\t\"logVolts\": {str(log.logvolts)},\n\t\"minVolts\": {log.minvolts},\n\t\"batteryLife\": {str(log.batteryLife)}\n }} ",'utf-8')
    }
    logframe = pd.DataFrame(data=log.readings,columns=['voltage_mV','current_mA','time_ms'])
    if "csv" in args:
        files['data.csv'] = bytes(logframe.to_csv(),'utf-8')
        if verbose:
            print("Created CSV file")

    if "tsv" in args:
        files['data.tsv'] = bytes(logframe.to_csv(sep="\t"),'utf-8')
        if verbose:
            print("Created TSV file")

    if "xml" in args:
        files['data.xml'] = bytes(logframe.to_xml(),'utf-8')
        if verbose:
            print("Created XML file")

    if "arrow" in args:
        arrowStream = io.BytesIO()
        logframe.to_feather(arrowStream)
        arrowStream.seek(0)
        files['data.arrow'] = arrowStream.read()
        arrowStream.close()
        if verbose:
            print("Created Arrow file")

    if "parquet" in args:
        parquetStream = io.BytesIO()
        logframe.to_parquet(parquetStream)
        parquetStream.seek(0)
        files['data.parquet'] = parquetStream.read()
        parquetStream.close()
        if verbose:
            print("Created Parquet file")

    if "orc" in args:
        files['data.orc'] = logframe.to_orc()
        if verbose:
            print("Created ORC file")

    if "json" in args:
        files['data.json'] = bytes(logframe.to_json(orient='records'),'utf-8')
        if verbose:
            print("Created JSON file")
    
    with tarfile.open(fileobj=dest,mode='w:gz' if compress else 'w') as tar:
        for filename,content in files.items():
            fileStream = io.BytesIO(content)
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            
            tar.addfile(tarinfo=tarinfo,fileobj=fileStream)
            if verbose:
                print(f"Archived {filename}")
            fileStream.close()
    
class exportTool:

    def __init__(self,args):
        self.args : dict = args #args should be a dict
        self.log : batteryTest = readlog(args["logpath"])
    
    @staticmethod
    def parse_args(args=None) -> dict:
        '''parses args, and returns them as a dict'''
        parser = argparse.ArgumentParser(
            description="Command line tool to process and export .bclog files"
        )
        subparsers = parser.add_subparsers(required=False)
        parser.add_argument("logpath",type=str,help="path to log file")
        parser.add_argument("-v","--verbose",action="store_true")
        parser.set_defaults(cmd="null")

        exportParser = subparsers.add_parser("E",help="export log as a tar archive",aliases=["export","tar"],add_help=True)
        exportParser.set_defaults(cmd="export")
        printCmd = subparsers.add_parser("P",help="Only prints the log on the console",aliases=["print", "display"])
        printCmd.set_defaults(cmd="print")
    
        exportParser.add_argument("-o","--outfile",help="name of the file to export to",type=str,default=None)
        exportParser.add_argument("-c","--compress",help="compress tar archive using gzip",action="store_true")
        exportParser.add_argument("--csv",help="export logs as a csv file",action="store_true")
        exportParser.add_argument("--tsv",help="export logs as a tsv file",action="store_true")
        exportParser.add_argument("--xml",help="export logs as an xml file",action="store_true")
        exportParser.add_argument("--arrow",help="export logs as an Arrow file",action="store_true")
        exportParser.add_argument("--parquet",help="export logs as a Parquet file",action="store_true")
        exportParser.add_argument("--orc",help="export logs as an orc file",action="store_true")
        exportParser.add_argument("--json",help="export logs as a json file",action="store_true")
        
        if args is not None:
            return vars(parser.parse_args(args=args))
        return vars(parser.parse_args())
    
    def process(self):
        '''processes arguments that were passed to the constructor'''
        match self.args["cmd"]:
            case "print":
                self.__display()
            case "export":
                if self.args["verbose"]:
                    self.__display()
                self.__export()

    def __display(self):
        #Prints log to console
        print(f"Retrieved {self.args['logpath']} at {time.strftime(f'%a %b %d %H:%M:%S%z %Y',time.localtime())}:")
        print(self.log)
        print("------------------------------------------------")
    
    def __export(self):
        #exports log to tar archive
        if not os.path.exists(f"./{config['system']['exdir']}"):
            os.mkdir(config['system']['exdir'])

        if self.args["outfile"] is None:
            exportname = f"{hex(self.log.fingerprint)[2:]}_{self.log.batteryID}_{time.strftime(f'%y%m%d-%H%M%S',self.log.timeStart)}.tar"
        else:
            exportname = f"{self.args['outfile']}.tar"
        
        if self.args["compress"]:
            exportname += '.gz'
        
        files = {
            'header.json' : bytes(f" {{ \n\t\"fingerprint\": \"{hex(self.log.fingerprint)}\",\n\t\"team\": \"{self.log.teamID}\",\n\t\"battery\": \"{self.log.batteryID}\",\n\t\"loadOhms\": {str(self.log.loadOhms)},\n\t\"startTime\": \"{self.log.getISO8601Timestamp()}\",\n\t\"pollTime\": {str(self.log.pollTime)},\n\t\"logVolts\": {str(self.log.logvolts)},\n\t\"minVolts\": {self.log.minvolts},\n\t\"batteryLife\": {str(self.log.batteryLife)}\n }} ",'utf-8')
        }
        if self.args["verbose"]:
            print(f"Exporting log {hex(self.log.fingerprint)[2:]} to ./{config['system']['exdir']}/{exportname}")
            print(f"----------------EXPORT SETTINGS-----------------\nCOMPRESSED: {self.args['compress']}\nCSV: {self.args['csv']}\nTSV: {self.args['tsv']}\nXML: {self.args['xml']}\nARROW: {self.args['arrow']}\nPARQUET: {self.args['parquet']}\nORC: {self.args['orc']}\nJSON: {self.args['json']}\n------------------------------------------------")

        logframe = pd.DataFrame(data=self.log.readings,columns=['voltage_mV','current_mA','time_ms'])

        if self.args["csv"]:
            files['data.csv'] = bytes(logframe.to_csv(),'utf-8')
            if self.args["verbose"]:
                print("Created CSV file")

        if self.args["tsv"]:
            files['data.tsv'] = bytes(logframe.to_csv(sep="\t"),'utf-8')
            if self.args["verbose"]:
                print("Created TSV file")

        if self.args["xml"]:
            files['data.xml'] = bytes(logframe.to_xml(),'utf-8')
            if self.args["verbose"]:
                print("Created XML file")

        if self.args["arrow"]:
            arrowStream = io.BytesIO()
            logframe.to_feather(arrowStream)
            arrowStream.seek(0)
            files['data.arrow'] = arrowStream.read()
            arrowStream.close()
            if self.args["verbose"]:
                print("Created Arrow file")

        if self.args["parquet"]:
            parquetStream = io.BytesIO()
            logframe.to_parquet(parquetStream)
            parquetStream.seek(0)
            files['data.parquet'] = parquetStream.read()
            parquetStream.close()
            if self.args["verbose"]:
                print("Created Parquet file")

        if self.args["orc"]:
            files['data.orc'] = logframe.to_orc()
            if self.args["verbose"]:
                print("Created ORC file")

        if self.args["json"]:
            files['data.json'] = bytes(logframe.to_json(orient='records'),'utf-8')
            if self.args["verbose"]:
                print("Created JSON file")


        with tarfile.open(f"./{config['system']['exdir']}/{exportname}",mode='x:gz' if self.args["compress"] else 'x') as tar:
            for filename,content in files.items():
                fileStream = io.BytesIO(content)
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(content)
                
                tar.addfile(tarinfo=tarinfo,fileobj=fileStream)
                if self.args["verbose"]:
                    print(f"Archived {filename} in ./{config['system']['exdir']}/{exportname}")
                fileStream.close()


if __name__ == '__main__':
    # Test command: python3 batconReader.py -v E -c --csv --tsv --xml --arrow --parquet --orc --json -o test ./logs/test2.bclog
    # Decompress commands (Unix terminal): 
    # cd exports
    # tar xf test.tar.gz
    # Test command 2: python3 batconReader.py -v P ./logs/test2.bclog
    tests = {
        'test1' : ["P","./logs/30ad0342_SIMBAT_241015-131109.bclog"],
        'test2' : ["-v","E",'-c','--csv','--tsv','--tsv','--xml','--arrow','--parquet','--orc','--json','-o','test','./testlogs/test.bclog']
    }
    args = exportTool.parse_args(args=tests['test1'])
    export = exportTool(args)
    export.process()

        
            
    



