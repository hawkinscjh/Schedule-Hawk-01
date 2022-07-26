from socket import *
import sys
import json
import csv
import os.path

def main(argv):
    # Catching incorrect inputs
    if(len(argv) != 2):
        print("Invalid number of arguments.")
        return
    elif(argv[1][-5:] != ".json"):
        print("This is not a JSON file. File argument must end in .json")
        return
    elif(not(os.path.exists(argv[1]))):
        print("This file path does not exits.")
        return
    # Opening and reading JSON data
    print("Getting Data from %s" % argv[1])
    with open(argv[1]) as input_file:
        data = json.load(input_file)
    
    # Naming and opening csv file
    outName = argv[1][:-5] + ".csv"
    outFile = open(outName, 'w', newline='')
    oWrite = csv.writer(outFile)

    print("Writing to %s" % outName)

    # Writing JSON data to csv file
    inc = 0
    for d in data:
        if inc == 0:
            oWrite.writerow(d.keys())
            inc += 1
        oWrite.writerow(d.values())
    
    outFile.close()
    print("Done")
            
if __name__ == '__main__':
    main(sys.argv)