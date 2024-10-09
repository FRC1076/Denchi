
static int voltages[] = {12000,11500,11000,10500,10000};
static int voltIndex = 0;

int batsim_getVoltage(){
    int res = voltages[voltIndex];
    voltIndex++;
    return res;
}