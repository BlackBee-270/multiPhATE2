#!/usr/bin/env python

################################################################
#
# summarizeCGPMresults.py
#
# Description:  This program parses a data file produced by queryCGPMresults.py,
#   which contains a slice through output generated by compareGeneProfiles_main.py
#   and postProcessCGPMresults.py, run in high-throughput using wrapper scripts.
#   Data were queried from a list of directories using queryCGPMresults.py.
#   summarizeCGPMresults.py extracts the genecall information for a designated reference
#   and lists it (one gene call per line) along with the corresponding (matching) gene
#   call information for the other strains/species against which PAK1 was compared.
#
# Programmer's Notes
#   This code was modified from a previously rather hard-coded version first written
#   in a big hurry due to extreme time constraints. This version should work properly
#   for an abritrary input reference genome and any number of other genomes to which
#   the reference was compared.
#
# Programmer: CEZhou
#    18 Nov 2013: begin
#    11 March 2014: Removed hard-coding and tested against PAK1 NxN data set
#    12 March 2014: Output goes to .out file rather than standard out
#*** 28 March 2014: Code has been added to accommodate reporting of loners
#          Note: this code (and query codes) should be re-cast using classes; right now it's a bit of
#          a jumble.  Also, using classes it should be simpler/easier to pull out
#          specific subsets of data, sorted.
#
################################################################
'''
'''

import sys
import re
import copy
from time import strftime
from time import gmtime
import os

dateTime = strftime("%Y:%m:%d::%H:%M:%S", gmtime())  # get time down to seconds
CODE_BASE_DIR = os.environ["CGP_CODE_BASE_DIR"]
##### FILES

infile = ""  # user provided
outfile = os.path.join(CODE_BASE_DIR, "summarizeCGPMresults.out")  # default
logfile = os.path.join(CODE_BASE_DIR, "summarizeCGPMresults.log")
LOGFILE = open(logfile,"w")
LOGFILE.write("%s%s\n" % ("Begin log file ",dateTime))
##### PATTERNS

#p_pattern = re.compile(' ')

##### DECLARATIONS

fileError = False

##### CONSTANTS

#LONER = False  # if query was for loner genes, no corresponding gene on other genome,
LONER = True   # which affects some code segments

PATH_FILE = int(5)      # identifies which word from input string from which to extract path/file
#ORGANISM_DIR = int(6)  # identifies which segment of the path/file from which to extract strains' dir
ORGANISM_DIR = ""       # change to penultimate /-delimited field of path/filename (compute below)
# The following are indexes to the fields in tabbed data line from input file containing mutual and singular hits
POSITION    = int(0)    # position at which hit was placed along reference genome (ie, sort position)
GENOME_TYPE = int(1)    # genome1|2 followed by "_" followed by  mutual|singular|loner
G1HEADER    = int(2)    # genome1 header
G1CONTIG    = int(3)
G1ANNOT     = int(4)    # list of annotations (as string; not being handled here)
G2HEADER    = int(5)    # genome2 header
G2CONTIG    = int(6)
G2ANNOT     = int(7)    # list of annotations (as string; not being handled here)
G1LENGTH    = int(8)    # length of G1 gene call
G2LENGTH    = int(9)    # length of G2 gene call
INTERPRETATION = int(10) # listing of interpretations (originally added by postProcessCGMP.py)
# The following indexes apply when the queryCGPMresults file contains loners
HEADER      = int(2)
CONTIG      = int(3)
ANNOTATION  = int(4)
LENGTH      = int(5)

HELP_STRING = "This script takes as input the name of a reference genome (ie, \'Sterne\') plus a file generated by queryCGPMresults.py, and produces output comprising genetic feature records for each genetic feature selected from the query. For each genetic feature of interest, the corresponding feature is identified for each genome that was compared. Fields displayed are: genome, header, annotation, length, and interpretation.  For more information, type: python summarizeCGPMresults.py usage|input\n"

USAGE_STRING = "Usage: summarizeCGPMresults.py <referenceGenome> <infile> <outfile>\nOutfile is optional. Default output file is summarizeCGPMresults.out"

INPUT_STRING = "Input: name of reference genome (ie, \'Sterne\') plus file containing query results generated by code queryCGPMresults.py. Caution: the reference genome should be spelled exactly as it is in the directory structure containing the comparison data sets.\n"

ACCEPTABLE_ARG_COUNT = (3,4) # 4 if user is providing name of output file 

#DEBUG = True
#DEBUG = False

##### VARIABLES

reference = "error"  # provided by user
otherGenome = "error"

myDict = {
    "myStuff" : "example",
    }

##### FUNCTIONS

def GetGeneData(genomeNumber, fields, geneDataInstance):
    # genomeNumber is '1' or '2'
    # fields is
    # geneDataInstance
    header                             = fields[G1HEADER]
    (locusTag,strand,start,end,extra)  = header.split('/')
    geneDataInstance["header"]         = header
    geneDataInstance["cds"]            = locusTag
    (junk,cdsNumber)                   = locusTag.split('cds')
    geneDataInstance["cdsNumber"]      = cdsNumber
    geneDataInstance["strand"]         = strand
    geneDataInstance["start"]          = start
    geneDataInstance["end"]            = end
    geneDataInstance["annotation"]     = fields[G1ANNOT]
    lengthString                       = fields[G1LENGTH]
    (junk, geneDataInstance["length"]) = lengthString.split('=')
    geneDataInstance["interpretation"] = fields[INTERPRETATION]
    return (geneDataInstance) 

##### GET INPUT PARAMETERS

argCount = len(sys.argv)
if argCount in ACCEPTABLE_ARG_COUNT:
    match = re.search("help", sys.argv[1].lower())
    if match:
        print (HELP_STRING)
        LOGFILE.close(); exit(0)
    match = re.search("input", sys.argv[1].lower())
    if match:
        print (INPUT_STRING)
        LOGFILE.close(); exit(0)
    match = re.search("usage", sys.argv[1].lower())
    if match:
        print (USAGE_STRING)
        LOGFILE.close(); exit(0)

    if argCount == 3:
        reference = sys.argv[1]
        infile = sys.argv[2] 
    elif argCount == 4:
        reference = sys.argv[1]
        infile = sys.argv[2] 
        outfile = sys.argv[3]
    else:
        print (USAGE_STRING)
        LOGFILE.close(); exit(0)
else:
    print (USAGE_STRING)
    LOGFILE.write("%s\n" % ("Incorrect number of command-line arguments provided"))
    LOGFILE.close(); exit(0)

# Open files
try:
    INFILE = open(infile,"r")
except IOError as e:
    fileError = True
    print (e)
try:
    OUTFILE = open(outfile,"w")
except IOError as e:
    fileError = True
    print (e)
if fileError:
    LOGFILE.close(); exit(0)


##### BEGIN MAIN 

# Additional Variables

genome = ""; hitType = ""
genome1 = ""; genome2 = ""; g1length = ""; g2length = ""
g1header = ""; g2header = ""; g1annot = ""; g2annot = ""
position = ""; genome_hitType = ""; interpretation = ""
words = []; pathFile = ""; segments = []; fields = []; lengthElements = []
junk = ""
cdsNumber = 0

referenceGeneList    = []  # will capture a non-redundant list of genes from input data
referenceHomologList = []  # will hold the lists of compared-genome genetic features data, indexed by order corresponding to referenceGeneList
comparedGenomesList  = []  # holds a non-redundant list of genomes that were compared to reference
geneExclusions       = {}  # key = header, value = exclusionList object 
exclusionList        = []  # holds list of genomes that reference gene is unique with respect to
geneAnnotation       = {}  # holds annotations for genes, key is compoundKey = header // contig
starts               = {}  # holds start locations (for sorting)

geneData = {
    "genome"         : "",  # genome with a corresponding genetic feature or gene 
    "header"         : "",
    "cds"            : "",
    "cdsNumber"      : 0,
    "strand"         : "",
    "start"          : 0,
    "end"            : 0,
    "contig"         : "",
    "annotation"     : "",
    "length"         : "",
    "interpretation" : "",
    }

homologData = {}  # holds a set of geneData objects

##### Read through input data file twice, first to collect all genetic features (ie, genes) for
##### the designated reference genome plus a non-redundant list of the genomes to which the
##### reference was compared, and then again to capture and organize all of the corresponding
##### genetic features from the compared genomes.
    
##### First pass:  collect all 1) compared genomes and 2) gene calls for reference genome into lists

fLines = INFILE.read().splitlines()
for line in fLines:
    match = re.search('Gene Set 1', line)        # Process each binary comparison
    words = []
    if match:                                    # Capture the 1st genome in the pair                      
        words = line.split(' ')
        pathFile = words[PATH_FILE]
        segments = pathFile.split('/')           # Split apart fully qualified path/filename
        genome1 = segments[-2]                   # sub-dir name for this genome's data is in penultimate position
        if genome1 not in comparedGenomesList:   # capture name of 1st compared genome
            if genome1 != reference:             # exclude reference from this list
                comparedGenomesList.append(genome1)
    match = re.search('Gene Set 2', line)        # Process each binary comparison
    if match:                                    # Capture the 2nd genome in the pair
        words = line.split(' ')
        pathFile = words[PATH_FILE]
        segments = pathFile.split('/')           # Split apart fully qualified path/filename
        genome2 = segments[-2]                   # sub-dir name for this genome's data is in penultimate position
        if genome2 not in comparedGenomesList:   # capture name of 2nd compared genome
            if genome2 != reference:             # exclude reference
                comparedGenomesList.append(genome2)

    match = re.search('^\d', line)               # Compile a list of all genes from reference
    if match:                                    # Line contains genetic feature data 
        fields = line.split('\t')
        (genome, hitType) = fields[GENOME_TYPE].split('_')
        if genome1 == reference:                 # Unless genome1 or genome2 is reference, don't bother 
            if not LONER:
                if fields[G1HEADER] not in referenceGeneList: # capture genetic feature / gene
                    referenceGeneList.append(fields[G1HEADER])
            if LONER:  # add gene to list only if this is a genome1_loner record
                if genome == 'genome1':
                    if fields[HEADER] not in referenceGeneList:  
                        referenceGeneList.append(fields[HEADER])   #*** ??? compoundKey here?
        if genome2 == reference:                 # Unless genome1 or genome2 is reference, don't bother
            if not LONER:
                if fields[G2HEADER] not in referenceGeneList: # capture genetic feature / gene
                    referenceGeneList.append(fields[G2HEADER]) 
            if LONER:  # add gene to list only if this is a genome2_loner record
                if genome == 'genome2':
                    if fields[HEADER] not in referenceGeneList:
                        referenceGeneList.append(fields[HEADER])

INFILE.close()

### The following section is needed only for mutual and singular hits
### For each reference gene found, create a data record and insert into a list in same order 

if not LONER:  # For mutual and singular hit data
    locusTag = ""; strand = ""; start = ""; end = ""; extra = ""
    headerFields = []
    for header in referenceGeneList:
        headerFields = header.split('/')
        locusTag = headerFields[0]
        strand   = headerFields[1]
        start    = headerFields[2]
        end      = headerFields[3]
        (junk,cdsNumber) = locusTag.split('cds')
        nextGeneData = copy.deepcopy(geneData)   # create empty data structure
        nextGeneData["header"]    = header
        nextGeneData["cdsNumber"] = cdsNumber
        nextGeneData["strand"]    = strand
        nextGeneData["start"]     = start
        nextGeneData["end"]       = end
        newHomologData = copy.deepcopy(homologData)
        newHomologData[reference] = nextGeneData # first item in the homolog list is the reference's own gene data
        referenceHomologList.append(newHomologData)  # place empty data structure; same index as header in homologGeneList 

### Second pass:  for each reference gene call, complete geneData record based on infile data

INFILE = open(infile,"r")
fLines = INFILE.read().splitlines()

if LONER:  # For detected unique genes on reference genome

    # First, create an empty exclusion list for each reference gene
    print ("Number of reference genes:", len(referenceGeneList))
    print ("Number of compared genomes:", len(comparedGenomesList))
    for header in referenceGeneList:
        newExclusionList = copy.deepcopy(exclusionList)
        geneExclusions[header] = newExclusionList

    # Second, determine genome1 and genome2 for next comparison set, then record genome exclusions for each reference gene
    for line in fLines:
        match = re.search('Gene Set 1', line)
        if match:
            words = line.split(' ')
            pathFile = words[PATH_FILE]
            segments = pathFile.split('/')
            genome1 = segments[-2]
        match = re.search('Gene Set 2', line)
        if match:
            words = line.split(' ')
            pathFile = words[PATH_FILE]
            segments = pathFile.split('/')
            genome2 = segments[-2]

        # For each reference loner gene in this list, record that the gene is unique wrt the other genome
        segments = []
        match = re.search('^\d', line)
        if match:
            fields = line.split('\t')
            (genome,hitType) = fields[GENOME_TYPE].split('_')
            if genome == 'genome1' and genome1 == reference:
                header = fields[HEADER]
                contig = fields[CONTIG]
                annot  = fields[ANNOTATION]
                contig_annotation = fields[CONTIG] + '_/_' + fields[ANNOTATION]
                geneExclusions[header].append(genome2) 
                geneAnnotation[header] = contig_annotation 
                segments = header.split('/')
                starts[header] = segments[2]
                #geneExclusions[header].append(genome2) 
            if genome == 'genome2' and genome2 == reference:
                header = fields[HEADER]
                contig = fields[CONTIG]
                annot  = fields[ANNOTATION]
                contig_annotation = fields[CONTIG] + '_/_' + fields[ANNOTATION]
                geneExclusions[header].append(genome1)
                geneAnnotation[header] = contig_annotation 
                segments = header.split('/')
                starts[header] = segments[2]
                #geneExclusions[header].append(genome1)

if not LONER:  # For mutual and singular hit data, record for each reference gene the corresponding genes from other genomes
    for line in fLines:
    
        # Determine which genome was #1 vs #2 
        match = re.search('Gene Set 1', line)
        if match:
            words = line.split(' ')
            pathFile = words[PATH_FILE]
            segments = pathFile.split('/')   # split apart fully qualified path/filename
            genome1 = segments[-2]           # name of organism's subdir is in penultimate position
        match = re.search('Gene Set 2', line)
        if match:
            words = line.split(' ')
            pathFile = words[PATH_FILE]
            segments = pathFile.split('/')   # split apart fully qualified path/filename
            genome2 = segments[-2]           # name of organism's subdir is in penultimate position

        # Gather a list of the genes that were selected from the genome of interest
        match = re.search('^\d', line)       # genetic-feature data lines begin with the position number
        if match:  # First, get handle on array index where geneData is kept; then store data
            referenceGeneData  = copy.deepcopy(geneData)
            otherGeneData      = copy.deepcopy(geneData)
            fields = line.split('\t')
            (genome,hitType) = fields[GENOME_TYPE].split('_')   

            if genome1 == reference:  # Unless genome1 or genome2 is reference, don't bother
                otherGenome = genome2 
                #*** Note: indexing by header is not necessarily unique (ie could be cds, start, end all same on different contigs, though highly unlikely)
                insertionPoint = referenceGeneList.index(fields[G1HEADER])  # get array index; corresponding locations!

                #*** Commented out code replaces redundant code below, but needs testing first !!!
                # Get Genome 1 data, put to reference data frame
                # referenceGeneData = GetGeneData(1,fields,referenceGeneData)
                # referenceHomologList[insertionPoint][reference] = referenceGeneData
                header                              = fields[G1HEADER]
                (locusTag,strand,start,end,extra)   = header.split('/') 
                referenceGeneData["header"]         = header
                referenceGeneData["cds"]            = locusTag
                (junk,cdsNumber)                    = locusTag.split('cds')
                referenceGeneData["cdsNumber"]      = cdsNumber
                referenceGeneData["strand"]         = strand
                referenceGeneData["start"]          = start
                referenceGeneData["end"]            = end
                referenceGeneData["annotation"]     = fields[G1ANNOT]
                lengthString                        = fields[G1LENGTH]
                (junk, referenceGeneData["length"]) = lengthString.split('=')
                referenceGeneData["interpretation"] = fields[INTERPRETATION]
                referenceHomologList[insertionPoint][reference] = referenceGeneData

                # Get Genome2 data, put to other genome's data frame
                # otherGeneData = GetGeneData(2,fields,referenceGeneData)
                # referenceHomologList[insertionPoint][otherGenome] = referenceGeneData
                header                            = fields[G2HEADER]
                (locusTag,strand,start,end,extra) = header.split('/') 
                otherGeneData["header"]           = header
                otherGeneData["cds"]              = locusTag
                (junk,cdsNumber)                  = locusTag.split('cds')
                otherGeneData["cdsNumber"]        = cdsNumber
                otherGeneData["strand"]           = strand
                otherGeneData["start"]            = start
                otherGeneData["end"]              = end
                otherGeneData["annotation"]       = fields[G2ANNOT]
                lengthString                      = fields[G2LENGTH]
                (junk, otherGeneData["length"])   = lengthString.split('=')
                otherGeneData["interpretation"]   = fields[INTERPRETATION]
                referenceHomologList[insertionPoint][otherGenome] = otherGeneData

            elif genome2 == reference:  # Unless genome1 or genome2 is reference, don't bother
                otherGenome = genome1
                insertionPoint = referenceGeneList.index(fields[G2HEADER])  # get array index; corresponding locations!

                # Get Genome 2 data, put to reference data frame
                # referenceGeneData = GetGeneData(2,fields,referenceGeneData)
                # referenceHomologList[insertionPoint][reference] = referenceGeneData
                header                              = fields[G2HEADER]
                (locusTag,strand,start,end,extra)   = header.split('/') 
                referenceGeneData["header"]         = header
                referenceGeneData["cds"]            = locusTag
                (junk,cdsNumber)                    = locusTag.split('cds')
                referenceGeneData["cdsNumber"]      = cdsNumber
                referenceGeneData["strand"]         = strand
                referenceGeneData["start"]          = start
                referenceGeneData["end"]            = end
                referenceGeneData["annotation"]     = fields[G2ANNOT]
                lengthString                        = fields[G2LENGTH]
                (junk, referenceGeneData["length"]) = lengthString.split('=')
                referenceGeneData["interpretation"] = fields[INTERPRETATION]
                referenceHomologList[insertionPoint][reference] = referenceGeneData

                # Get Genome1 data, put to other genome's data frame
                # otherGeneData = GetGeneData(1,fields,referenceGeneData)
                # referenceHomologList[insertionPoint][otherGenome] = referenceGeneData
                header                            = fields[G1HEADER]
                (locusTag,strand,start,end,extra) = header.split('/') 
                otherGeneData["header"]           = header
                otherGeneData["cds"]              = locusTag
                (junk,cdsNumber)                  = locusTag.split('cds')
                otherGeneData["cdsNumber"]        = cdsNumber
                otherGeneData["strand"]           = strand
                otherGeneData["start"]            = start
                otherGeneData["end"]              = end
                otherGeneData["annotation"]       = fields[G1ANNOT]
                lengthString                      = fields[G1LENGTH]
                (junk, otherGeneData["length"])   = lengthString.split('=')
                otherGeneData["interpretation"]   = fields[INTERPRETATION]
                referenceHomologList[insertionPoint][otherGenome] = otherGeneData

    # Check results

    listSize = len(referenceGeneList)
    OUTFILE.write("%s%s\n" % ("Number of entries in referenceGeneList",len(referenceGeneList)))
    OUTFILE.write("%s\n" % ("Genome\tHeader\tAnnotation\tLength\tInterpretation"))
    #print "Number of entries in referenceGeneList:", len(referenceGeneList)
    #print "Genome\tHeader\tAnnotation\tLength\tInterpretation\t"
    for i in xrange(0,listSize-1):
        OUTFILE.write("%s%s\n" % ("Gene No. ", i+1))
        #print "Gene No.", i+1
        if "header" in referenceHomologList[i][reference]:   #
            header = referenceHomologList[i][reference]["header"]
            annotation = referenceHomologList[i][reference]["annotation"]
            length = referenceHomologList[i][reference]["length"]
            interpretation = referenceHomologList[i][reference]["interpretation"]
            OUTFILE.write("%s\t%s\t%s\t%s\t%s\n" % (reference,header,annotation,length,interpretation))
            #print reference, "\t", header, '\t', annotation, '\t', length, '\t', interpretation 
            if "header" in referenceHomologList[i][reference]:
                for otherGenome in comparedGenomesList:
                    if otherGenome in referenceHomologList[i]:
                        header = referenceHomologList[i][otherGenome]["header"]
                        annotation = referenceHomologList[i][otherGenome]["annotation"]
                        length = referenceHomologList[i][otherGenome]["length"]
                        interpretation = referenceHomologList[i][otherGenome]["interpretation"]
                        OUTFILE.write("%s\t%s\t%s\t%s\t%s\n" % (otherGenome,header,annotation,length,interpretation))
                        #print otherGenome, "\t", header, '\t', annotation, '\t', length, '\t', interpretation 
                    else:
                        OUTFILE.write("%s%s\n" % (otherGenome,": no record found"))
                        #print otherGenome, ": no record found"
        else:
            OUTFILE.write("%s%s\n" % (reference,": no record found"))
            #print reference, ": no record found"

        OUTFILE.write("%s\n" % ("################################################"))
        #print "###################################################"

if LONER:  # Print out a list of reference genome loners and the compared genomes that they are unique with respect to
    # First, alphabetize the compared genomes list and write header line in output file
    comparedGenomesList.sort()
    OUTFILE.write("%s\t%s\t%s\t%s" % ("Reference genetic feature","Start","Contig","Annotation"))
    for genome in comparedGenomesList:
        OUTFILE.write("\t%s" % (genome))
    OUTFILE.write("\n")

    # Next, prepare to write chart of reference genes vs. compared genomes
    for header in geneExclusions:
        printArray = []
        for j in xrange(0,len(comparedGenomesList)):
             printArray.append('')
        (contig,annotation) = geneAnnotation[header].split('_/_')
        OUTFILE.write("%s\t%s\t%s\t%s" % (header,starts[header],contig,annotation))
        for genome in geneExclusions[header]:
            i = comparedGenomesList.index(genome)
            printArray[i] = 'X'
        #OUTFILE.write("%s" % printArray)
        for item in printArray:
            OUTFILE.write("\t%s" % (item))  
        OUTFILE.write("\n")
            
##### CLEAN UP

INFILE.close()
OUTFILE.close()
dateTime = "0:0:0:0:0:0"
dateTime = strftime("%Y:%m:%d::%H:%M:%S", gmtime())  # get time down to seconds
#dateTime = str(datetime.datetime.now().time()) # get time down to sub-seconds
#dateTime = os.popen('date')
LOGFILE.write("%s%s\n" % ("Processing complete ",dateTime))
LOGFILE.close()
