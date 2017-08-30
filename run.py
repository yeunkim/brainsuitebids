#!/opt/conda/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import os
import shutil
import nibabel
from glob import glob
from subprocess import Popen, PIPE, check_output
from shutil import rmtree
import subprocess
from bids.grabbids import BIDSLayout
from functools import partial
from collections import OrderedDict
import time
from multiprocessing import Process, Pool
import logging
import datetime
import traceback
import sys
from bin.brainsuiteWorkflowNoQC import runWorkflow

def run(command, env={}, cwd=None):
    merged_env = os.environ
    merged_env.update(env)
    merged_env.pop("DEBUG", None)
    print(command)
    process = Popen(command, stdout=PIPE, stderr=subprocess.STDOUT,
                    shell=True, env=merged_env, cwd=cwd)
    while True:
        line = process.stdout.readline()
        line = str(line)[:-1]
        print(line)
        if line == '' and process.poll() != None:
            break
    if process.returncode != 0:
        raise Exception("Non zero return code: %d"%process.returncode)

def callrunshell(**args):
    # `dirname $0`/qsubWrapper.sh `dirname $0` "${dataFile}" "${dwiBase}" "${subjectDerivativeBase}" "${PUBLIC}" "${bdp}" "${svreg}" "${newTemp}"
    print(args)
    args.update(os.environ)
    cmd = '/qsubWrapper.sh ' + \
          '{inputDir} ' + \
            '{dataFile} ' + \
            '{dwiBase} ' + \
            '{subjectDerivativeBase} ' + \
            '{PUBLIC} ' + \
            '{bdp}' + \
            '{svreg} ' + \
            '{newTemp}'
    cmd = cmd.format(**args)
    run(cmd, cwd=args["path"], env={"OMP_NUM_THREADS": str(args["n_cpus"])})

__version__ = open('/qc-system/version').read()

parser = argparse.ArgumentParser(description='BrainSuite17a Pipelines BIDS App (T1w, dMRI)')
parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('output_dir', help='The directory where the output files '
                    'should be stored. If you are running group level analysis '
                    'this folder should be prepopulated with the results of the'
                    'participant level analysis.')
parser.add_argument('analysis_level', help='Level of the analysis that will be performed. '
                    'Multiple participant level analyses can be run independently '
                    '(in parallel) using the same output_dir.',
                    choices=['participant'])
parser.add_argument('--participant_label', help='The label of the participant that should be analyzed. The label '
                   'corresponds to sub-<participant_label> from the BIDS spec '
                   '(so it does not include "sub-"). If this parameter is not '
                   'provided all subjects should be analyzed. Multiple '
                   'participants can be specified with a space separated list.',
                   nargs="+")
parser.add_argument('-v', '--version', action='version',
                    version='BrainSuite17a Pipelines BIDS App version {}'.format(__version__))


args = parser.parse_args()

run("bids-validator " + args.bids_dir, cwd=args.output_dir)

layout = BIDSLayout(args.bids_dir)
subjects_to_analyze = []

if not os.path.exists(args.output_dir):
    os.mkdir(args.output_dir)

# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
else:
    subject_dirs = glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]

if args.analysis_level == "participant":
    for subject_label in subjects_to_analyze:
        t1ws = [f.filename for f in layout.get(subject=subject_label,
                                               type='T1w',
                                               extensions=["nii.gz", "nii"])]
        dwis = [f.filename for f in layout.get(subject=subject_label,
                                               type='dwi',
                                               extensions=["nii.gz", "nii"])]
        assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

        # TODO: support multiple sessions : ? sessions = layout.get(target='ses' )
        for i, t1 in enumerate(t1ws):
            dwi = dwis[0].split('.')[0]

            runWorkflow('sub-%s'%subject_label, args.output_dir, 'BDP', 'SVREG')



