MAX_VOLTAGE = 13.3

class fake0MPC3008:
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
    
    test_data = [ MAX_VOLTAGE, 12, 11, 10.8, 11, 12, MAX_VOLTAGE]
    b = fake0MPC3008(test_data)
    for t in test_data:
        assert(b.voltage() == t)

