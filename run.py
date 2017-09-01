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
from shutil import copyfile
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

            sessions = layout.get(target='session', return_type='id',
                                  subject=subject_label,
                                  type='T1w',
                                  extensions=["nii.gz","nii"]
                                  )

            if len(sessions) > 0:
                for ses in range(0, len(sessions)):
                    # layout._get_nearest_helper(dwi, 'bval', type='dwi')
                    t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                           type='T1w', session=sessions[ses],
                                                           extensions=["nii.gz", "nii"])]
                    assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

                    dwis = [f.filename for f in layout.get(subject=subject_label,
                                                           type='dwi', session=sessions[ses],
                                                           extensions=["nii.gz", "nii"])]
                    if (len(dwis) > 0):
                        for i, t1 in enumerate(t1ws):
                            abspath = os.path.abspath(t1)
                            bvals = [f for f in layout._get_nearest_helper(abspath,
                                                                           'bval',
                                                                           type='dwi')]
                            bvecs = [f for f in layout._get_nearest_helper(abspath,
                                                                           'bvec',
                                                                           type='dwi')]
                            dwipath = os.path.abspath(os.path.dirname(dwis[i]))
                            copyfile(bvals[0], os.path.join(dwipath, 'tmp.bval'))
                            copyfile(bvecs[0], os.path.join(dwipath,'tmp.bvec'))

                            subjectID = 'sub-{0}_ses-{1}'.format(subject_label, sessions[ses])
                            runWorkflow(subjectID, t1, args.output_dir, args.bids_dir, BDP=dwis[i].split('.')[0], SVREG=True)
                            os.remove(os.path.join(dwipath, 'tmp.bval'))
                            os.remove(os.path.join(dwipath, 'tmp.bvec'))

                    else:
                        for t1 in t1ws:
                            runWorkflow('sub-%s'%subject_label, t1, args.output_dir, args.bids_dir, SVREG=True)
            else:

                t1ws = [f.filename for f in layout.get(subject=subject_label,
                                                       type='T1w',
                                                       extensions=["nii.gz", "nii"])]
                assert (len(t1ws) > 0), "No T1w files found for subject %s!" % subject_label

                dwis = [f.filename for f in layout.get(subject=subject_label,
                                                       type='dwi',
                                                       extensions=["nii.gz", "nii"])]
                if (len(dwis) > 0):
                    for i, t1 in enumerate(t1ws):
                        abspath = os.path.abspath(t1)
                        bvals = [f for f in layout._get_nearest_helper(abspath,
                                                                       'bval',
                                                                       type='dwi')]
                        bvecs = [f for f in layout._get_nearest_helper(abspath,
                                                                       'bvec',
                                                                       type='dwi')]
                        dwipath = os.path.abspath(os.path.dirname(dwis[i]))
                        copyfile(bvals[0], os.path.join(dwipath, 'tmp.bval'))
                        copyfile(bvecs[0], os.path.join(dwipath, 'tmp.bvec'))
                        runWorkflow('sub-%s' % subject_label, t1, args.output_dir, args.bids_dir,
                                    BDP=dwis[i].split('.')[0], SVREG=True)
                        os.remove(os.path.join(dwipath, 'tmp.bval'))
                        os.remove(os.path.join(dwipath, 'tmp.bvec'))

                else:
                    for t1 in t1ws:
                        runWorkflow('sub-%s' % subject_label, t1, args.output_dir, args.bids_dir, SVREG=True)

