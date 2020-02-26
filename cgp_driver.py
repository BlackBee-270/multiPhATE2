#!/usr/bin/env python

#######################################################
#
# CGPMdriver.py - command-line version 1.0.0 (/multiPhATE2/)
#
# Programmer:  Carol L. Ecale Zhou
#
# Last update: 21 February 2020
#
# This script inputs a config file, cgpNxN.config, which lists the
# base directory containing input fasta and annotation files for
# processing through compareGeneProfiles_main.py.
#
# CGPMdriver.py reads the input config file and handles all downstream
# processing of the CompareGeneProfiles pipeline. Overall the pipeline
# processes are as follows:
# 0) Take as input, file cgpNxN.config, then...
# 1) Run code constructConfigFile.py to generate file, CGPMwrapper.config
# 2) Run code CGPMwrapper.py with input file CGPMwrapper.config
#    This executes each pairwise comparison... 
#    Generating the following output files in each pairwise comparison directory (cn):
#    - compareGeneProfiles_main.log
#    - compareGeneProfiles_main.report
#    - compareGeneProfiles_main.summary 
#    - blast result files for each binary comparison
#    Generating a set of files in each genome's subdirectory (gn):
#    - gene fasta
#    - protein fasta
#    - gene blast database files
#    - protein blast database files
# 3) Run code constructPPcgpmConfigFile.py to create ppCGPMwrapper.config
# 4) Run code ppCGPMwrapper.py with input file ppCGPMwrapper.config 
#
#################################################################
'''
'''

import sys, os, re, string, copy
import datetime, time
from subprocess import call

##### CONSTANTS and CONFIGURABLES
CODE_BASE_DIR = os.environ["PHATE_BASE_DIR"] + "CompareGeneProfiles/"     # Location of this and subordinate codes
CONSTRUCT_CONFIG_FILE_CODE = os.path.join(CODE_BASE_DIR, "constructConfigFile.py")
COMPARE_GENE_PROFILES_WRAPPER_CODE = os.path.join(CODE_BASE_DIR, "CGPMwrapper.py")

# Set environmental variables for CGP's dependent codes
os.environ["CGP_CODE_BASE_DIR"] = CODE_BASE_DIR

ACCEPTABLE_ARG_COUNT = (2,) #  

HELP_STRING = "This code is a wrapper for running the compareGeneProfiles pipeline over several genome comparisons.\nInput the fully qualified pathname to the project directory where the code should execute.\n"

INPUT_STRING = "Provide as input the fully qualified directory path to the users project directory.\nPrepare your config file to specify the following information:\nLine 1: The fully qualified path of the project directory\nLines 2-n: name of each genome and its corresponding annotation file, separated by a single space,\nprepended with the name of the subdirectory for this genome-annotation pair.\n"

USAGE_STRING = "Usage:  CGPMdriver.py project_directory_pathname"

##### Variables

userProjectDir = os.environ["PHATE_PIPELINE_OUTPUT_DIR"] # This is where CGP output is to be written 

#### FILES

logFile = os.path.join(CODE_BASE_DIR, "CGPMdriver.log")
LOGFILE = open(logFile,"a")
LOGFILE.write("%s\n" % ("==================================="))
today = os.popen('date')
LOGFILE.write("%s%s\n" % ("Begin log file at ",today.read()))
in_configFilename    = "cgpNxN.config"
cgpm_configFilename = "CGPMwrapper.config"
cgpm_configFile = ""

##### Get command-line arguments
argCount = len(sys.argv)
if argCount in ACCEPTABLE_ARG_COUNT:  
    match = re.search("help", sys.argv[1].lower())
    if match:
        print (HELP_STRING)
        exit(0)
    match = re.search("input", sys.argv[1].lower())
    if match:
        print (INPUT_STRING)
        exit(0)
    match = re.search("usage", sys.argv[1].lower())
    if match:
        print (USAGE_STRING)
        exit(0)
    # If not a help string, argument should be absolute path to input configuration file 
    in_configFile = sys.argv[1]
else:
    print (USAGE_STRING)
    exit(0)

##### Set absolute path/file for config files
projectDirectory = os.path.dirname(in_configFile) 
cgpm_configFile = os.path.join(projectDirectory, cgpm_configFilename)
LOGFILE.write("%s%s\n" % ("User project directory is ",projectDirectory))
LOGFILE.write("%s%s\n" % ("Input config file is ", in_configFile))
LOGFILE.write("%s%s\n" % ("Output config file is ", cgpm_configFile))

##### Parse config file; construct lists of BASE_DIRS and FILES

print("Opening in_configFile",in_configFile)
IN_CONFIG_FILE = open(in_configFile,"r")
today = os.popen('date')
LOGFILE.write("%s%s\n" % ("Compare Gene Profiles pipeline execution start time is ",today.read()))
LOGFILE.write("%s%s%s%s\n" % ("Executing Step 1: Running code constructConfigFile.py with ", in_configFile, " to generate file ", cgpm_configFile))
print ("Executing Step 1...")
command = "python " + CONSTRUCT_CONFIG_FILE_CODE + " " + in_configFile + " " + cgpm_configFile
os.system(command)
print ("Step 1 complete.")

LOGFILE.write("%s%s\n" % ("Executing Step 2: Running code ",COMPARE_GENE_PROFILES_WRAPPER_CODE))
LOGFILE.write("%s%s\n" % ("...with parameter project directory: ",projectDirectory))
LOGFILE.write("%s\n" % ("...to generate report and accessory files..."))
today = os.popen('date')
LOGFILE.write("%s%s\n" % ("Executing Step 2 at ",today.read()))
print ("Executing Step 2...")
command = "python " + COMPARE_GENE_PROFILES_WRAPPER_CODE + " " + projectDirectory
LOGFILE.write("%s%s\n" % ("Running command: ",command))
os.system(command)
print ("Step 2 complete.")

today = os.popen('date')
LOGFILE.write("%s%s\n" % ("Step 2 execution complete at ",today.read()))
print ("Execution of ppCGPM (steps 3 and 4) are currently manual")

##### Clean up

LOGFILE.close()


