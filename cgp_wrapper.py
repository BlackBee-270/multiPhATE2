#!/usr/bin/env python

#######################################################
#
# CGPMwrapper.py (/multiPhATE2/)
#
# Programmer:  Carol L. Ecale Zhou
# Last Update: 12 April 2020
#
# This script uses a config file to run compareGeneProfiles.py
# using the designated input files.  Specifically, the config file
# contains a base directory followed by 2 genome filenames and 2
# annotation filenames (see example below). Note that the input config
# file to CGPMwrapper.py can be auto-generated by constructConfigFile.py,
# which in turn inputs a config file consisting of a base directory
# followed by a list of genome/annotation-file pairs, one per line, with
# the genome and annotation filenames separated by ' '.   
# Pending further upgrades, CGPMwrapper.py accepts all default parameters
# of compareGeneProfiles_main.py
# 
# Config file format example with 3 jobs:
#
#/home/zhou4/BacGenomeStudies/StrainA  
#/Genomes/<Strain_dir>/<genome1_file> 
#/Genomes/<Strain_dir>/<genome2_file>  
#/RAST/<Strain_dir>/<gff1_file>    
#/RAST/<Strain_dir>/<gff2_file>  
#/home/zhou4/BacGenomeStudies/StrainA/Results   
#<blank line>
#/home/zhou4/BacGenomeStudies/StrainA  
#/Genomes/<Strain_dir>/<genome1_file> 
#/Genomes/<Strain_dir>/<genome3_file> 
#/RAST/<Strain_dir>/<gff1_file>       
#/RAST/<Strain_dir>/<gff3_file>        
#/home/zhou4/BacGenomeStudies/StrainA/Results  
#<blank line>
#/home/zhou4/BacGenomeStudies/StrainA  
#/Genomes/<Strain_dir>/<genome2_file> 
#/Genomes/<Strain_dir>/<genome3_file>  
#/RAST/<Strain_dir>/<gff2_file>    
#/RAST/<Strain_dir>/<gff3_file>     
#/home/zhou4/BacGenomeStudies/StrainA/Results  
#
# Caution: insert blank lines between job file sets, no comments
#
# There is one set of the above input parameters for each comparison
# to be run.
#
#
#################################################################
'''
'''

import sys, os, re, string, copy
import time
from subprocess import call

##### CONFIGURABLES
CODE_BASE_DIR = os.environ["CGP_CODE_BASE_DIR"]
PHATE_PIPELINE_OUTPUT_DIR = os.environ["PHATE_PIPELINE_OUTPUT_DIR"]
COMPARE_GENE_PROFILES_CODE = os.path.join(CODE_BASE_DIR, "cgp_compareGeneProfiles_main.py")  # use current stable version or modify constant

# Set messaging booleans
PHATE_PROGRESS = False
PHATE_MESSAGES = False
PHATE_WARNINGS = False
PHATE_PROGRESS_STRING = os.environ["PHATE_PHATE_PROGRESS"]
PHATE_MESSAGES_STRING = os.environ["PHATE_PHATE_MESSAGES"]
PHATE_WARNINGS_STRING = os.environ["PHATE_PHATE_WARNINGS"]
if PHATE_PROGRESS_STRING.lower() == 'true':
    PHATE_PROGRESS = True
if PHATE_MESSAGES_STRING.lower() == 'true':
    PHATE_MESSAGES = True
if PHATE_WARNINGS_STRING.lower() == 'true':
    PHATE_WARNINGS = True

#### FILE

logFile = os.path.join(CODE_BASE_DIR,"CGPMwrapper.log")
LOGFILE = open(logFile,"a")
LOGFILE.write("%s\n" % ("================================"))
LOGFILE.write("%s\n" % ("Begin CGPMwrapper log file"))

#### CONSTANTS

ACCEPTABLE_ARG_COUNT = (2,) # "help" or user project directory absolute path expected

HELP_STRING = "This code is a wrapper for conveniently running compareGeneProfiles_main.py over several genome comparisons.\n"

INPUT_STRING = "Prepare your config file to specify the following information:\nFor each comparison, list the base directory, genome #1, genome #2, annotation file #1, and annotation file #2, each on a line of text, and skip one line between comparison sets.\nRun this wrapper from the appropriate directory!\ne.g., /home/zhou4/BacGenomeStudies/PAK1/CompareGeneProfiles/Comparisons/\nFor a sample config file, look at configFile_sample.\nNote:  You may prefer to automatically generate the config file using script constructConfigFile.py\n"

USAGE_STRING = "Usage:  cgp_wrapper.py <userDirectory>"

##### Variables

projectDirectory = ""  # user's project directory, passed by calling code (i.e., CGPMdriver.py)
configFile = "cgp_wrapper.config"  # needs to be prepended with user's project directory

##### Get command-line arguments

if PHATE_PROGRESS:
    print("cgp_wrapper says, Being processing.")
    print("cgp_wrapper says, Gathering command-line arguments.")
argCount = len(sys.argv)
if argCount in ACCEPTABLE_ARG_COUNT:
    match = re.search("help", sys.argv[1].lower())
    if match:
        print (HELP_STRING)
        exit(0)
    match = re.search("input", sys.argv[1].lower())
    match2 = re.search("config", sys.argv[1].lower())  # note: config file may have 'input' string in filename
    if match and not match2:
        print (INPUT_STRING)
        exit(0)
    match = re.search("usage", sys.argv[1].lower())
    if match:
        print (USAGE_STRING)
        exit(0)
    else:
        projectDirectory = sys.argv[1]
        LOGFILE.write("%s%s\n" % ("Project directory is ", projectDirectory))
else:
    print (USAGE_STRING)
    exit(0)

##### Parse config file; construct lists of BASE_DIRS and FILES

configFile = os.path.join(PHATE_PIPELINE_OUTPUT_DIR, configFile) # prepend the directory path to user's directory
LOGFILE.write("%s%s\n" % ("Parsing configFile: ",configFile))
CONFIG_FILE = open(configFile,"r")

inFiles  = {
    "dir" : "", # directory where the genome (g1, g2) and annotation (a1, a2) files sit
    "cdir": "", # directory where the configuration comparision result files site
    "g1"  : "",
    "g2"  : "",
    "a1"  : "",
    "a2"  : "",
    } 
inFileList = [] # list of inFile dicts

##### Walk through the config file, extracting the directory plus the genome/annotation pairs
##### Add each pair to the list to be processed by compareGeneProfiles_main.py
    
if PHATE_PROGRESS:
    print("cgp_wrapper says, Parsing config file.")
fLines = CONFIG_FILE.read().splitlines()
numLines = len(fLines)
LOGFILE.write("%s%s\n" % ("Number of lines in config file is ",numLines))
nextFiles = copy.deepcopy(inFiles)
for i in list(range(0, numLines)):
    if i%7 == 0:
        nextFiles["dir"] = fLines[i]
    elif i%7 == 1:
        nextFiles["g1"] = fLines[i]
    elif i%7 == 2:
        nextFiles["g2"] = fLines[i]
    elif i%7 == 3:
        nextFiles["a1"] = fLines[i]
    elif i%7 == 4:
        nextFiles["a2"] = fLines[i]
    elif i%7== 5:
        nextFiles["cdir"] = fLines[i]
    elif i%7 == 6:
        inFileList.append(nextFiles)
        nextFiles = copy.deepcopy(inFiles)
CONFIG_FILE.close()
LOGFILE.write("%s%s\n" % ("inFileList is:",inFileList))

##### For each set, execute compareGeneProfiles_main.py

currentTime = int(time.time())
LOGFILE.write("%s%s\n" % ("Executing compareGeneProfiles_main.py at ",currentTime))
if PHATE_PROGRESS:
    print ("cgp_wrapper says, Executing compareGeneProfiles_main.py....")
count = 0
for fileSet in inFileList:
    count += 1
    directory = fileSet["dir"]
    genome1   = fileSet["g1"]; genome1 = os.path.join(directory, genome1)  # Need to prepend project dir to get full path
    genome2   = fileSet["g2"]; genome2 = os.path.join(directory, genome2)
    annot1    = fileSet["a1"]; annot1  = os.path.join(directory, annot1)
    annot2    = fileSet["a2"]; annot2  = os.path.join(directory, annot2)
    LOGFILE.write("%s\n" % ("Calling compareGeneProfiles_main.py with the following input parameters:\n"))
    LOGFILE.write("%s%s\n" % ("-g1 genome1: ",genome1))
    LOGFILE.write("%s%s\n" % ("-g2 genome2: ",genome2))
    LOGFILE.write("%s%s\n" % ("-a1 annot1:  ",annot1))
    LOGFILE.write("%s%s\n" % ("-a2 annot2:  ",annot2))
    LOGFILE.write("%s%s\n" % ("-d  userDir: ",projectDirectory))
    call(["python",COMPARE_GENE_PROFILES_CODE,"-g1",genome1,"-g2",genome2,"-a1",annot1,"-a2",annot2,"-d",projectDirectory])

currentTime = int(time.time())
LOGFILE.write("%s%s%s%s\n" % ("Execution complete. ",count," jobs completed at ",currentTime))
if PHATE_PROGRESS:
    print ("cgp_wrapper says, Execution complete.", count, "jobs completed.")

##### Clean up

LOGFILE.close()

