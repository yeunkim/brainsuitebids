# -*- coding: utf-8 -*-
"""
checks.py

Performs all initial checks required before allowing run.sh to begin spawning processes.
This includes verifying that:
    Nipype is installed correctly
    BrainSuite is installed correctly
    Specified directory adheres to essentials of BIDS structure
        Must contain all subject folders specified in participants.tsv
            Each subject folder contains anat/sub-<num>_T1w.nii.gz file

returns:
    0 on success
    1 on failure


Usage:
python checks.py participants_tsv_file

"""

from __future__ import unicode_literals, print_function
from builtins import str

#Checking brainsuite executable path
from distutils.spawn import find_executable
#Path set properly if reached here
from nipype import config #Set configuration before importing nipype pipeline
cfg = dict(execution={'remove_unnecessary_outputs' : False}) #We do not want nipype to remove unnecessary outputs
config.update_config(cfg)

import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
import nipype.interfaces.io as io
import os

import sys
from optparse import OptionParser

from distutils.spawn import find_executable


# Checks for BrainSuite executables installed. Return True if installed, False else.
#If True, sets brainsuite_atlas_directory to appropiate value
def verifyBrainsuiteInstalled():
    if(find_executable('bse') and find_executable('svreg.sh') and find_executable('bdp.sh')):
        brainsuite_atlas_directory = find_executable('bse')[:-3] + '../atlas/' #Will not use here, but run this to make sure we can find our atlas directory
        return True
    else:
        print('Your system path has not been set up correctly.')
        print('Please add the above paths to your system path variable and restart the kernel for this tutorial.')
        print('Edit your ~/.bashrc file, and add the following line, replacing your_path with the path to BrainSuite16a1:\n')
        print('export PATH=$PATH:/your_path/BrainSuite16a1/svreg/bin:/your_path/BrainSuite16a1/bdp:/your_path/BrainSuite16a1/bin')
        return False


def createSubjectDirectory(base, subject):
    """Returns base/subject"""
    return base + os.sep + subject

def parseInput():
    """#Parses arguments, tries to read file passed in
    If error reading file, or file not exist, prints out error message, return false
    If file empty print error message, return false
    Parses file structure file, validates existance of directories, and files. If error, prints out error message, return false

    Return true if all passed
    """

    version_msg = "%prog 1.0"
    usage_msg = """
%prog subjectsFile
Expected format of subjectsFile:
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

    participantsFile = None
    try:
        participantsFile = open(args[0], "r")
    except FileNotFoundError:
        print("Error: the file: %s is not found" % args[0])
        return False

    baseDirectory = os.path.dirname(args[0])
    subjectDirectories = []

    firstTime = True
    subjectNameIndex = -1
    rowLength = -1
    lineCount = 0
    for line in participantsFile:
        lineCount = lineCount + 1
        line = line.strip()
        if line != "":
            if firstTime:
                header = line.split()
                if header.count("participant_id") != 1:
                    print("Error in participants.tsv file. Header row must contain a participant_id column")
                    return False
                
                subjectNameIndex = line.split().index("participant_id")
                rowLength = len(header)
                firstTime = False
            else:
                currentRow = line.split()
                if len(currentRow) != rowLength:
                    print("Column formatting error in participant.tsv file, in line %d." % lineCount)
                    return False
                currentSubjID = currentRow[subjectNameIndex]
                checkDirectory = createSubjectDirectory(baseDirectory, currentSubjID)
                if not os.path.isdir(checkDirectory):
                    print("Error: the following path is not an existing directory: %s" % checkDirectory)
                    return False
                
                subjectDirectories.append(currentSubjID)

    if(not firstTime and len(subjectDirectories) != 0):
        print("Successfully validated structure of dataset")
        return True
    else:
        print("participants.tsv file is empty or does not list any participants")
        return False


if __name__ == "__main__":
    if not verifyBrainsuiteInstalled():
        exit(1)

    if not parseInput():
        exit(1)

    exit(0)
