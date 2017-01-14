# -*- coding: utf-8 -*-
"""
genStatusFile.py

Parses subjectsFile, then scans all status.txt files indicated by subjectsFile
Generates json file based on status of each subject
Continuously loops until all subjects have completed. See global DONE_STATE variable

returns:
    0 on success
    1 on failure


Usage:
python genStatusFile.py subjectsFile

subjectsFile expected format:
    Path to Data directory
    Subject_dir_1
    ...
    Subject_dir_n

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

def createSubjectDirectory(base, subject):
    """Returns base/subject"""
    return base + os.sep + subject

def createSubjectDataPath(base, subject):
    """Returns base/subject/subject.nii.gz"""
    return base + os.sep + subject + os.sep + subject + ".nii.gz"

def createStatusPath(subject):
    return WORKFLOW_BASE_DIRECTORY + os.sep + subject + os.sep + STATUS_NAME

def createBrainSuiteStatePath():
    return WORKFLOW_BASE_DIRECTORY + os.sep + "brainsuite_state.json"


def parseInput():
    """#Parses arguments, tries to read file passed in
    If error reading file, or file not exist, prints out error message, return false
    If file empty print error message, return false
    Parses file structure file, validates existance of directories, and files. If error, prints out error message, return false

    Return true if all passed
    """

    version_msg = "%prog 1.0"
    usage_msg = """
%prog DataStructureFile
DataStructureFile expected format:
    Path to Data directory
    Subject_dir_1
    ...
    Subject_dir_n
"""

    parser = OptionParser(version=version_msg, usage=usage_msg)
    options, args = parser.parse_args(sys.argv[1:])
    if len(args) != 1:
        parser.error("Expected 1 argument, got %s" % len(args))
        return False

    structureFile = None
    try:
        structureFile = open(args[0], "r")
    except FileNotFoundError:
        print("Error: the file: %s is not found" % args[0])
        return False


    firstTime = True
    global SUBJECTS
    for line in structureFile:
        line = line.strip()
        if line != "":
            if firstTime:
                if not os.path.isdir(line):
                    print("Error: the following path is not an existing directory: %s" % line)
                    return False
                global WORKFLOW_BASE_DIRECTORY
                WORKFLOW_BASE_DIRECTORY = line
                firstTime = False
            else:
                SUBJECTS.append(line)


def generateJSON():
    global START_TIME
    global START_TIME_STRING

    j = {}
    j['status'] = 'TODO'
    if START_TIME is None:
        START_TIME = datetime.now()
        START_TIME_STRING = str(START_TIME).rsplit(".", 1)[0]
    j['start_time'] = START_TIME_STRING
    j['update_time'] = 'TODO'
    j['runtime'] = str(datetime.now() - START_TIME).rsplit(".", 1)[0]
    j['path_to_thumbnails'] = PATH_TO_THUMBNAILS

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

    parseInput()
    
    print("Creating file %s" % createBrainSuiteStatePath())
    print("Continuously looping, and updating this status file until all processing is complete.")

    while not ALL_DONE:
        jsonToWrite = generateJSON()
        brainsuiteState = open(createBrainSuiteStatePath(), 'w')
        brainsuiteState.write(jsonToWrite)
        brainsuiteState.close()
        time.sleep(1)



    print("All subjects complete.")
    exit(0)
