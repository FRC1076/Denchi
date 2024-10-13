# Denchi

## The Battery Conditioner   (aka BATCON)

The battery conditioner has five main components.

1.  The controller (a Raspberry Pi)
2.  The voltage monitor (an Analog to Digital Converter (ADC) connected to the Raspberry Pi via the Serial Peripheral Interface (SPI) protocol)
3.  The load (power resistors configured to provide a 6 Ohm load sinking approximately 2 Amps during the conditioning/capacity measurement phase)
4.  A 6 Amp battery charger capable of fully charging a competition battery in 4-6 hours.
5.  One or more relays to permit the controller to choose between a load (or loads if we expand to have more than one load), and the battery charger.

## Battery conditioning

Battery conditioning (and capacity measurement) is a fairly simple task.

1. A fully charged battery is connected to the device
2. The controller instructs a relay to connect the battery to a load so the battery starts discharging
3. The controller monitors the voltage vi the ADC of the battery as it discharges, recording the information over time
4. At the designated "empty" voltage level, the controller records the end of the discharge phase, disconnects the battery from the load, and connects the battery to a battery charger.
5. The controller processes all of the time and voltage data from the discharge phase and uses it to create a report of the battery capacity.   (this requires some simple math to compute the integral of the current over time (current is voltage times the load resistance).   The result of the integral is the battery capacity in Amps times hours, or Ah.

## Performance Requirements (Wish List)

1. The batcon should not destroy the battery.    For example, if the batcon crashes, the battery should be left charging the battery (not draining it until death).
2. batcon should record the report in a useful form so it may be read by other tools to analyze the data in the report.
3. batcon should monitor it's own activity to detect if something has gone wrong.   It should gracefully shut down and leave the battery connected to the charger.   It should send a notification to an operator if anything unusual is detected.
4. batcon should be able to perform a short self-test (a few minutes in length).


## Development Plan


* Oct 4
	- install pytest and run ADCtest.py to see it work  (if you run pytest --help, you can get lots of options, although -s is probably the main one you might want to use)
        - write one additional test of some kind just for practice
	- write a simple program that accepts a filename as an argument as well as a team number and puts a header entry into the file
        
		e.g.    

```
> python batcon.py --id '2025A' --team 1076 --loadohms 6.1 --outfile history.dat
> cat history.dat
# batcon Battery Conditioner and Capacity Test
# TeamID: 1076
# BatteryID: 2025A
# LoadOhms: 6.1
# StartTime: Sat Sep 28 12:00:12 EDT 2024
>
```
	- you can use the python argparse library (see numerous simple examples via search)
 
* Oct 11
	- extend the batcon.py so it accepts a time interval for polling data from one of the fake data sources and reads the data from it at that interval (--interval 100) would read from the data source every 100ms, for example.
	- extend the output to write out the data with timestamps (using time.time()) and the voltage reading in comma,delimited format.    Write one record per line in the same --outfile after the header
	- internally, just make up the data by using one of the fakeADC data sources with some specified values
        - write the code to compute the battery capacity as indicated by the fake data.  Write a unit test to verify that it computes the correct capacity.   Note that with a small amount of data, and a short interval, the battery capacity may end up being a very small number (when expressed as Amp Hours (Ah).

* Oct 18
	- create a class for the relay object "SMRI.Relay" that takes a pin as an argument and does the necessary setup and manipulation of the relay via a reasonable API.     Maybe consider .set(0) and .set(1) for Off and On to be like wpilib conventions. Define some enum constants similarly to wpilib.   e.g.  SMRI.Relay.On
        - Save the definition in SMRI.py so you can import the implementation as:
	from SMRI import Relay

        - enhance batcon to keep a running total of the battery depletion (in units of amps * seconds)  For this you will need to apply the trapezoidal method to find the product of the *current* (which is determined by dividing the voltage reading by the load (in Ohms)) and the *time*, which is the time between the start and end of the interval.

	- display the total (convert it into amps * hours) in a final line in the --outfile

```
# Total battery capacity (in Ah): 10.52
```

* Oct 25
