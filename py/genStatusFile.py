# -*- coding: utf-8 -*-
"""
genStatusFile.py

Parses subjectsFile, then scans all status.txt files indicated by subjectsFile
Generates json file based on status of each subject
Saves json file into Derivatives/brainsuite_state.json
Continuously loops until all subjects have completed. See global DONE_STATE variable

returns:
    0 on success
    1 on failure


Usage:
python genStatusFile.py participants_tsv_file public_html
public_html, the path to save brainsuite_state.json

"""

from __future__ import unicode_literals, print_function
from builtins import str



import os, sys, json, time
from datetime import datetime
from optparse import OptionParser


WORKFLOW_BASE_DIRECTORY = ""
SUBJECTS = []
PATH_TO_THUMBNAILS = "/thumbnails/"
STATUS_NAME = "status.txt"

ALL_DONE = False

DONE_STATE = "11"


#For timing
START_TIME = None
START_TIME_STRING = ""

def createStatusPath(subject):
    return WORKFLOW_BASE_DIRECTORY + os.sep + subject + os.sep + STATUS_NAME

def createBrainSuiteStatePath():
    return PUBLIC + os.sep + "brainsuite_state.json"

def parseInput():
    """#Parses arguments, tries to read file passed in
    If error reading file, or file not exist, prints out error message, return false
    If file empty print error message, return false
    Parses file structure file, validates existance of directories, and files. If error, prints out error message, return false

    Return true if all passed
    """
    version_msg = "%prog 1.0"
    usage_msg = """
%prog participants_tsv_file
"""

    parser = OptionParser(version=version_msg, usage=usage_msg)
    options, args = parser.parse_args(sys.argv[1:])
    if len(args) != 2:
        parser.error("Expected exactly 2 arguments, got %s" % len(args))
        return False

    participantsFile = None
    try:
        participantsFile = open(args[0], "r")
    except:
        print("Error accessing file %s: %s" % (args[0], sys.exc_info()[0]))
        return False

    global WORKFLOW_BASE_DIRECTORY
    global PUBLIC
    WORKFLOW_BASE_DIRECTORY = os.path.dirname(args[0]) + os.sep + "Derivatives"
    PUBLIC = os.path.abspath(args[1])

    firstTime = True
    subjectNameIndex = -1;
    global SUBJECTS
    for line in participantsFile:
        line = line.strip()
        if line != "":
            if firstTime:
                subjectNameIndex = line.split().index("participant_id")
                firstTime = False
            else:
                SUBJECTS.append(line.split()[subjectNameIndex])

    return True

def generateJSON(processingComplete):
    global START_TIME
    global START_TIME_STRING

    j = {}
    if START_TIME is None:
        START_TIME = datetime.now()
        START_TIME_STRING = str(START_TIME).rsplit(".", 1)[0]

    if processingComplete:
        j['status'] = "All processing complete"
    else:
        j['status'] = "Processing in progress"
    
    j['start_time'] = START_TIME_STRING
    j['runtime'] = str(datetime.now() - START_TIME).rsplit(".", 1)[0]
    j['thumbnails_abspath'] = PUBLIC + os.sep + PATH_TO_THUMBNAILS
    #relativepath is relative to where index.html will be placed
    j['thumbnails_relativepath'] = PATH_TO_THUMBNAILS

    subjectsJSONArray = []
    seenNotDone = False
    for s in SUBJECTS:
        currentJson = {}
        currentJson['name'] = s

        statusFile = open(createStatusPath(s), 'r')
        currentState = statusFile.read()
        currentState = currentState.strip()
        if not currentState == DONE_STATE:
            seenNotDone = True
        statusFile.close()
        currentJson['state'] = currentState
        subjectsJSONArray.append(currentJson)

    j['subjects'] = subjectsJSONArray

    if not seenNotDone:
        global ALL_DONE
        ALL_DONE = True
    return json.dumps(j)

if __name__ == "__main__":

    if not parseInput():
        print("Error parsing inputs")
        exit(1)
    
    print("Creating file %s" % createBrainSuiteStatePath())
    print("Continuously looping, and updating this status file until all processing is complete.")

    while not ALL_DONE:
        jsonToWrite = generateJSON(False)
        brainsuiteState = open(createBrainSuiteStatePath(), 'w')
        brainsuiteState.write(jsonToWrite)
        brainsuiteState.close()
        time.sleep(1)

    #Generate final completed stage
    jsonToWrite = generateJSON(True)
    brainsuiteState = open(createBrainSuiteStatePath(), 'w')
    brainsuiteState.write(jsonToWrite)
    brainsuiteState.close()

    print("All subjects complete.")
    exit(0)

