MILLIVOLTS_PER_VOLT = 1000
def V2mV(volts):
    return int(volts * MILLIVOLTS_PER_VOLT)

#
#   All values in millivolts to make everything integers
#
MAX_VOLTAGE = V2mV(13.3)
MIN_VOLTAGE = V2mV(10.5)
DEFAULT_STEP = 50

#
# Use pytest to run all functions that contain test_ in the name
#
# pytest testADC.py    --  runs test without print output (unless it fails)
# pytest -s testADC.py --  runs test always containing print output
#
# Check out pytest options to up your game

"""
Acts as a fake MPC3008.   A list of numbers passed through the
constructor provides the readings to be returned on each call.
"""
class fake0MPC3008:
    """
    If DATA is omitted, or is empty, the voltage() call always returns MAX_VOLTAGE
    DATA should be an indexable list of voltage values.
    """
    def __init__(self, data=None):
        self.reading_index = 0
        self.data = data
    
    def voltage(self):
        print("Getting voltage   index:", self.reading_index)
        try:
            current_reading = self.data[self.reading_index]
        except:
            current_reading = MAX_VOLTAGE
        self.reading_index+=1

        print("Got reading: ", current_reading)
        return current_reading
    


def test_fake0MPC3008():

    a = fake0MPC3008()
    assert(a.voltage() == MAX_VOLTAGE)
    assert(a.voltage() == MAX_VOLTAGE)
    
    test_data = [ MAX_VOLTAGE, 12000, 11000, 10800, 11000, 12000, MAX_VOLTAGE]
    b = fake0MPC3008(test_data)
    for t in test_data:
        assert(b.voltage() == t)


class fake1MPC3008():
    """
    This fake data source accepts a MIN, MAX, and STEP and serves up
    the voltage values starting with max down STEP wise until hitting MIN,
    and then STEP wise back up to MAX.
    """
    def __init__(self, Vmin=MIN_VOLTAGE, Vmax=MAX_VOLTAGE, step=DEFAULT_STEP):
        self.vmax = Vmax
        self.vmin = Vmin
        self.step = step
        self.reading = Vmax
        self.charge_direction = -1
        self.seqnum = 1


    def voltage(self):
        current_reading = self.reading

        if current_reading <= self.vmin:
            print(self.seqnum, ": Bottomed out at:", current_reading)
            current_reading = self.vmin
            self.reading = self.vmin
            self.charge_direction=1   # switch to  charging

        # use the step and direction to compute next reading
        self.reading+=(self.charge_direction * self.step)
        print(self.seqnum, ": Next reading computed:", self.reading)    

        # give steady MAX_VOLTAGE when done
        if self.charge_direction==1 and self.reading >= self.vmax:
            self.reading=MAX_VOLTAGE

        print(self.seqnum, ": Reading:", current_reading)
        self.seqnum+=1
        return current_reading
    


def test_fake1MPC3008():

    # create with no args (use defaults)
    a = fake1MPC3008()
    r = MAX_VOLTAGE

    # check it on the way down
    while r >= MIN_VOLTAGE:
        assert(r == a.voltage())
        r-=DEFAULT_STEP
    else:
        r+=DEFAULT_STEP
    
    #
    # The a.voltage() call above already turned around with an increase
    # And it also decremented the r.   We have to catch up with
    # another increment.     Probably a small bug here.

    r+=DEFAULT_STEP
    while r <= MAX_VOLTAGE:
        assert(r == a.voltage())
        r+=DEFAULT_STEP





    


    

