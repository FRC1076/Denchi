from flask import Flask, render_template, request, jsonify, Response
from batcon import fakeBatconFactory
import json
import time
'''
a flask server that acts as a backend to the web client. Uses dummy battery for not
'''

app = Flask(__name__)

def readingGenerator(id,loadohms,minvolts,logvolts,team,polltime):
    batconfac = fakeBatconFactory(id,loadohms,minvolts,logvolts,team,polltime)
    batconfac.writeHeader()
    voltage_mV = 10000000000000000000000000000000000
    logfile = batconfac.getOutputFile()
    batlogger = batconfac.getFSBatlogger(logfile)
    batlogger.start()
    while (voltage_mV > batlogger.header.minvolts):
        reading = batlogger.recordReading() #(voltage_mV,current_mA,time_ms)
        voltage_V = reading[0]/1000
        current_A = reading[1]/1000
        time_ms = reading[2]
        print(reading)
        chunk = {"voltage_V" : voltage_V, "current_A" : current_A, "time_ms" : time_ms}
        yield json.dumps(chunk)
        time.sleep(batlogger.header.pollTime/1000)
    batlife = batlogger.end()/3600
    logfile.close()
    print(f"# Battery Life (Amp-Hours): {batlife}")
    with open(batconfac.outfilepath,'a') as f:
        f.write(f'# Battery Life (Amp-Hours): {batlife}\n')
    return batlife

@app.route('/')
def mainpage():
    return render_template('mainpage.html')

@app.route('/process', methods=['POST'])
def startLogging():
    json_data = request.get_json()
    id = json_data.get('id')
    loadohms = json_data.get('loadohms')
    minvolts = json_data.get('minvolts')
    logvolts = json_data.get('logvolts')
    team = json_data.get('team')
    polltime = json_data.get('polltime')
    print(json_data)
    return Response(readingGenerator(id,loadohms,minvolts,logvolts,team,polltime), mimetype='text/event_stream')

if __name__ == '__main__':
    app.run(debug=True)