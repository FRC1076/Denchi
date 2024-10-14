from dataclasses import dataclass
import time
import argparse
import tarfile
import io
import pandas as pd
import tomli

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



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Command line tool to process and export .bclog files"
    )
    subparsers = parser.add_subparsers(required=False)
    parser.add_argument("logpath",type=str,help="path to log file")
    parser.add_argument("-v","--verbose",action="store_true")
    parser.set_defaults(export=False)

    exportParser = subparsers.add_parser("E",help="export log as a tar archive",aliases=["Export","Tar"])
    exportParser.set_defaults(export=True)
    
    exportParser.add_argument("-o","--outfile",help="name of the file to export to",type=str,default=None)
    exportParser.add_argument("-c","--compress",help="compress tar archive using gzip",action="store_true")
    exportParser.add_argument("-n","--name",help="Name of the exported files",type=str,default=None,dest="exportname")
    exportParser.add_argument("--csv",help="export logs as a csv file",action="store_true")
    exportParser.add_argument("--tsv",help="export logs as a tsv file",action="store_true")
    exportParser.add_argument("--xml",help="export logs as an xml file",action="store_true")
    exportParser.add_argument("--arrow",help="export logs as an Arrow file",action="store_true")
    exportParser.add_argument("--parquet",help="export logs as a Parquet file",action="store_true")
    exportParser.add_argument("--hdf",help="export logs as an hdf5 file",action="store_true")
    exportParser.add_argument("--orc",help="export logs as an orc file",action="store_true")
    exportParser.add_argument("--json",help="export logs as a json file",action="store_true")

    args = parser.parse_args()
    log = readlog(args.logpath)
    if args.verbose:
        print(f"Retrieved {args.logpath} at {time.strftime(f'%a %b %d %H:%M:%S%z %Y',time.localtime())}:")
        print(log)
        print("------------------------------------------------")

    if args.export:

        if args.outfile is None:
            exportname = f"{hex(log.fingerprint)[2:]}_{log.batteryID}_{time.strftime(f'%y%m%d-%H%M%S',log.timeStart)}.tar"
        else:
            exportname = f"{args.out}"
        
        if args.compress:
            exportname += '.gz'
        
        files = {
            'header.txt' : bytes(f"# Battery Conditioner and Capacity Test\n# Fingerprint: {hex(log.fingerprint)[2:]}\n# Team Number: {log.teamID}\n# Battery ID: {log.batteryID}\n# Load (Ohms): {str(log.loadOhms)}\n# Start Time: {log.getTimestamp()}\n# Poll Interval: {str(log.pollTime)}\n# Delta-V Logging Threshold: {str(log.logvolts)}\n# Minimum Volts: {log.minvolts}\n# Battery Life (Ampere-Hours): {str(log.batteryLife)}\n",'ascii')
        }
        if args.verbose:
            print(f"Exporting log {hex(log.fingerprint)[2:]} to ./{config['system']['exdir']}/{exportname}")
            print(f"----------------EXPORT SETTINGS-----------------\nCOMPRESSED: {args.compress}\nCSV: {args.csv}\nTSV: {args.tsv}\nXML: {args.xml}\nARROW: {args.arrow}\nJSON: {args.json}\n")

        logframe = pd.DataFrame(data=log.readings,columns=['voltage_mV','current_mA','time_ms'])

        if args.csv:
            files['data.csv'] = bytes(logframe.to_csv())
            if args.verbose:
                print("Created CSV file")

        if args.tsv:
            files['data.tsv'] = bytes(logframe.to_csv(sep="\t"))
            if args.verbose:
                print("Created TSV file")

        if args.xml:
            files['data.xml'] = bytes(logframe.to_xml())
            if args.verbose:
                print("Created XML file")

        if args.arrow:
            arrowStream = io.BytesIO()
            logframe.to_feather(arrowStream)
            arrowStream.seek(0)
            files['data.arrow'] = arrowStream.read()
            arrowStream.close()
            if args.verbose:
                print("Created Arrow file")

        if args.parquet:
            parquetStream = io.BytesIO()
            logframe.to_parquet(parquetStream)
            parquetStream.seek(0)
            files['data.parquet'] = parquetStream.read()
            parquetStream.close()
            if args.verbose:
                print("Created Parquet file")

        if args.hdf:
            hdf5Stream = io.BytesIO()
            logframe.to_hdf(hdf5Stream)
            hdf5Stream.seek(0)
            files['data.hdf5'] = hdf5Stream.read()
            hdf5Stream.close()
            if args.verbose:
                print("Created HDF5 file")

        if args.orc:
            files['data.orc'] = logframe.to_orc()
            if args.verbose:
                print("Created ORC file")

        if args.json:
            files['data.json'] = bytes(logframe.to_json())
            if args.verbose:
                print("Created JSON file")


        with tarfile.open(f"./{config['system']['exdir']}/{exportname}",mode='x:gz' if args.compress else 'x') as tar:
            for filename,content in files.items():
                fileStream = io.BytesIO(content)
                tarinfo = tarfile.TarInfo(name=filename)
                tarinfo.size = len(content)
                
                tar.addfile(tarinfo=tarinfo,fileobj=fileStream)
                if args.verbose:
                    print(f"Archived {filename} in ./{config['system']['exdir']}/{exportname}")
                fileStream.close()
        

            



        
            
    



