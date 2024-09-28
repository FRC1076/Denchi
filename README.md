# Denchi
Battery conditioning

Development Plan

* Oct 4
	- install pytest and run ADCtest.py to see it work  (if you run pytest --help, you can get lots of options, although -s is probably the main one you might want to use)
        - write one additional test of some kind just for practice
	- write a simple program that accepts a filename as an argument as well as a team number and puts a header entry into the file
		e.g.    

$ python batconcap.py --id '2025A' --team 1076 --loadohms 6.1 --outfile history.dat
$ cat history.dat
# batconcap Battery Conditioner and Capacity Test
# TeamID: 1076
# BatteryID: 2025A
# LoadOhms: 6.1
# StartTime: Sat Sep 28 12:00:12 EDT 2024
$
	- you can use the python argparse library (see numerous simple examples via search)
 
* Oct 11
	- extend the batconcap.py so it accepts a time interval for polling data from one of the fake data sources and reads the data from it at that interval (--interval 100) would read from the data source every 100ms, for example.
	- extend the output to write out the data with timestamps (using time.time()) and the voltage reading in comma,delimited format.    Write one record per line in the same --outfile after the header
	- internally, just make up the data by using one of the fakeADC data sources with some specified values

* Oct 18
	- create a class for the relay object SMRI.Relay that takes a pin as an argument and does the necessary setup and manipulation of the relay via a reasonable API.     Maybe consider .set(0) and .set(1) for Off and On to be like wpilib conventions.
	- Save the definition in SMRI.py so you can import the implementation as:
	from SMRI import Relay

        - enhance batconcap to keep a running total of the battery depletion (in units of amps * seconds)  For this you will need to apply the trapezoid method to find the product of the current (which is determined by dividing the voltage reading by the load (in ohms) and the time, which is the time between the start and end of the interval.

	- display the total (convert it into amps * hours) in a final line in the --outfile

	# Total battery capacity (in Ah): 10.52

* Oct 25
