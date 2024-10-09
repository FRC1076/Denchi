#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "batsim.h"

static char doc[] = "FRC 1076 Battery Conditioning\nThis takes a series of voltages from an integer stream (generally a stream of voltage readings from a battery, or a file of preset test voltages), and records battery data to a character stream (generally an ascii file)";
static char inputFilepath[] = "batteryVoltages.dat";
static int currentVoltage;

struct arguments {
    char *batID;
    double loadohms;
    char *teamID;
    char *filepath;
    int polltime;
};

void sleep_ms(int milliseconds) {
    Sleep(milliseconds); // Sleep function from Windows API
}

void parse_arguments(int argc, char **argv, struct arguments *arguments) {
    // Set default values of options
    arguments->teamID = "1076";
    arguments->filepath = "history.dat";
    arguments->polltime = 100;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--team") == 0 && i + 1 < argc) {
            arguments->teamID = argv[++i];
        } else if (strcmp(argv[i], "--outfile") == 0 && i + 1 < argc) {
            arguments->filepath = argv[++i];
        } else if (strcmp(argv[i], "--interval") == 0 && i + 1 < argc) {
            arguments->polltime = atoi(argv[++i]);
        } else if (i == 1) {
            arguments->batID = argv[i];
        } else if (i == 2) {
            arguments->loadohms = atof(argv[i]);
        } else {
            fprintf(stderr, "Invalid argument: %s\n", argv[i]);
            exit(EXIT_FAILURE);
        }
    }

    if (arguments->batID == NULL || arguments->loadohms <= 0) {
        fprintf(stderr, "Usage: %s BATTERY LOADOHMS\n", argv[0]);
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char **argv) {
    FILE *fptr; // Output file pointer
    time_t now = time(NULL);
    struct arguments arguments = {0}; // Initialize to zero

    parse_arguments(argc, argv, &arguments);

    // Open output file
    fptr = fopen(arguments.filepath, "a");
    if (!fptr) {
        fprintf(stderr, "Error opening file: %s\n", arguments.filepath);
        return EXIT_FAILURE;
    }
    
    fprintf(fptr, "------------------------------------------------\n");
    fprintf(fptr, "# Fingerprint: PLACEHOLDER\n# TeamID: %s\n# BatteryID: %s\n# LoadOhms: %f\n# StartTime: %s# PollTime: %d\n",
            arguments.teamID, arguments.batID, arguments.loadohms, ctime(&now), arguments.polltime);
    
    for (int i = 0; i < 5; i++) {
        currentVoltage = batsim_getVoltage();
        fprintf(fptr, "%f,%f,%ld\n",
                ((double)currentVoltage) / 1000,
                ((double)currentVoltage) / (1000 * arguments.loadohms),
                clock()); // Time is given in milliseconds since the beginning of execution
        sleep_ms(arguments.polltime);
    }
    
    fprintf(fptr, "Battery Life: PLACEHOLDER\n");
    fclose(fptr);
    return EXIT_SUCCESS;
}