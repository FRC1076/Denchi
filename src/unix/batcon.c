#include <stdio.h>
#include <stdlib.h>
#include <argp.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "batsim.h"

static char doc[] = "FRC 1076 Battery Conditioning\nThis takes a series of voltages from an integer stream (generally a stream of voltage readings from a battery, or a file of preset test voltages), and records battery data to a character stream (generally an ascii file)";
static char args_doc[] = "BATTERY LOADOHMS";
static char inputFilepath[] = "batteryVoltages.dat";
static int currentVoltage;

struct arguments {
    char *batID;
    double loadohms;
    char *teamID;
    char *filepath;
    int polltime;
};

void sleep_ms(int milliseconds)
{
    // Convert milliseconds to microseconds
    usleep(milliseconds * 1000);
}

/* The options that we are checking for */
static struct argp_option options[] = {
    {"team", 't', "teamID", 0, "The team number (defaults to 1076)"},
    {"outfile", 'o', "filepath", 0, "The path to the output file (defaults to 'history.dat')"},
    {"interval", 'i', "polltime", 0, "The interval (in milliseconds) between pollings (defaults to 100ms)"},
    {0}
};

static error_t parse_opt(int key, char *arg, struct argp_state *state) {
    char *endptr;
    struct arguments *arguments = (struct arguments *)state->input; // Explicit cast

    switch (key) {
        case 't':
            arguments->teamID = arg;
            break;
        case 'o':
            arguments->filepath = arg;
            break;
        case 'i':
            arguments->polltime = strtol(arg, &endptr, 10);
            if (endptr == arg) {
                fprintf(stderr, "Invalid value for polltime\n");
                argp_usage(state);
            }
            break;

        case ARGP_KEY_ARG:
            if (state->arg_num >= 2) {
                argp_usage(state);
            }
            switch (state->arg_num) {
                case 0:
                    arguments->batID = arg;
                    break;
                case 1:
                    arguments->loadohms = strtod(arg, &endptr);
                    if (endptr == arg) {
                        fprintf(stderr, "Invalid value for LOADOHMS\n");
                        argp_usage(state);
                    }
                    break;
            }
            break;

        case ARGP_KEY_END:
            if (state->arg_num < 2) {
                argp_usage(state);
            }
            break;

        default:
            return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp argp = {options, parse_opt, args_doc, doc};

int main(int argc, char **argv) {
    FILE *fptr; //output file pointer
    time_t now = time(NULL);
    struct arguments arguments = {0}; // Initialize to zero

    // Set default values of options
    arguments.teamID = "1076";
    arguments.filepath = "history.dat";
    arguments.polltime = 100;

    argp_parse(&argp, argc, argv, 0, 0, &arguments);

    //open output file
    fptr = fopen(arguments.filepath,"a");
    fprintf(fptr,"------------------------------------------------\n");
    fprintf(fptr,"# Fingerprint: PLACEHOLDER\n# TeamID: %s\n# BatteryID: %s\n# LoadOhms: %f\n# StartTime: %s# PollTime: %d\nVoltage,Current,Timestamp\n",
    arguments.teamID,arguments.batID,arguments.loadohms,ctime(&now),arguments.polltime);
    for (int i = 0; i < 5; i++){
        currentVoltage = batsim_getVoltage();
        fprintf(fptr,"%f,%f,%ld\n",
        ((double)currentVoltage)/1000,
        ((double)currentVoltage)/(1000*arguments.loadohms),
        clock()); //Time is given in microseconds since the beginning of execution
        sleep_ms(arguments.polltime);
    }
    fprintf(fptr,"Battery Life: PLACEHOLDER\n");
    fclose(fptr);
    return EXIT_SUCCESS;
}
