# -*- coding: utf-8 -*-
"""
checks.py

Performs all initial checks required before allowing run.sh to begin spawning processes.
This includes verifying that:
    Nipype is installed correctly
    BrainSuite is installed correctly
    All folders in subjects file exist
    All folders in subjects file contain subjectName.nii.gz data


returns:
    0 on success
    1 on failure


Usage:
python checks.py subjectsFile

subjectsFile expected format:
    Path to Data directory
    Subject_dir_1
    ...
    Subject_dir_n

"""

from __future__ import unicode_literals, print_function
#from builtins import str

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


brainsuite_atlas_directory = ""

baseDirectory = ""
subjectDirectories = []

# Checks for BrainSuite executables installed. Return True if installed, False else.
#If True, sets brainsuite_atlas_directory to appropiate value
def verifyBrainsuiteInstalled():
    if(find_executable('bse') and find_executable('svreg.sh') and find_executable('bdp.sh')):
        brainsuite_atlas_directory = find_executable('bse')[:-3] + '../atlas/'
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

def createSubjectDataPath(base, subject):
    """Returns base/subject/subject.nii.gz"""
    return base + os.sep + subject + os.sep + subject + ".nii.gz"


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
    for line in structureFile:
        line = line.strip()
        if line != "":
            if firstTime:
                if not os.path.isdir(line):
                    print("Error: the following path is not an existing directory: %s" % line)
                    return False

                baseDirectory = line
                firstTime = False
            else:
                checkDirectory = createSubjectDirectory(baseDirectory, line)
                checkFile = createSubjectDataPath(baseDirectory, line)
                if not os.path.isdir(checkDirectory):
                    print("Error: the following path is not an existing directory: %s" % checkDirectory)
                    return False
                if not os.path.isfile(checkFile):
                    print("Error while validating file structure: following file does not exist: %s " % checkFile)
                    return False

                subjectDirectories.append(line)

    if(not firstTime and len(subjectDirectories) != 0):
        print("Successfully validated structure of data folder using file: %s" % args[0])
        return True
    else:
        print("Data structure file is empty or does not list any folders")
        return False


if __name__ == "__main__":
    if not verifyBrainsuiteInstalled():
        exit(1)

    if not parseInput():
        exit(1)


    exit(0)
