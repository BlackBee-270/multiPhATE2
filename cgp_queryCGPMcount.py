#!/usr/bin/env python

#######################################################
#
# queryCGPMcount.py
#
#
# Programmer:  Carol L. Ecale Zhou
# Last update:  14 November 2013
# 
#
#################################################################
'''
'''

import sys, os, re, string, copy
from subprocess import call

#### FILES
CODE_BASE_DIR = os.environ["CGP_CODE_BASE_DIR"]
logFile = os.path.join(CODE_BASE_DIR, "queryCGPMcount.log")
LOGFILE = open(logFile,"w")
LOGFILE.write("%s\n" % ("Begin log file"))

#### CONSTANTS

HELP_STRING = "Script queryCGPMcount.py counts the number of genetic differences between pairs of genomes, given as input a file produced by script queryCGPMresults.py\n" 

USAGE_STRING = "Usage:  python queryCGPMcount.py queryFile.out (generated by queryCGPMresults.py)\n"

INPUT_STRING = "Input:  file generated by queryCGPMresults.py\n"

# Open user file, parse, count

queryFile = sys.argv[1]
QUERY_FILE = open(queryFile,"r")

count = 0
fLines = QUERY_FILE.read().splitlines()
for line in fLines:
    match = re.search('^#',line)
    if match:
        print (line)
        match2 = re.search('Gene Set 2',line)
        if match2:
            print (count)
            count = 0
    else:
        count += 1

QUERY_FILE.close()
LOGFILE.close()

