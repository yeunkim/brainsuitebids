# -*- coding: utf-8 -*-
"""
cse.py

Python script to run BrainSuite Cortical Surface Extraction routine
To be called after validating data structure using checks.py

Returns:
    0 on successful processing run
    1 on failure

Usage:
python cse.py DataBaseDirectory

DataBaseDirectory represents base directory of a subject; should directly contain subjects .nii.gz data
Example: %prog ~/Documents/webapp/Data/1000
Expects no trailing slash
"""


from __future__ import unicode_literals, print_function
from builtins import str

#Checking brainsuite executable path
from distutils.spawn import find_executable
#Path set properly if reached here
from nipype import config #Set configuration before importing nipype pipeline
from nipype.interfaces.utility import Function
cfg = dict(execution={'remove_unnecessary_outputs' : False}) #We do not want nipype to remove unnecessary outputs
config.update_config(cfg)

import nipype.pipeline.engine as pe
import nipype.interfaces.brainsuite as bs
import nipype.interfaces.io as io
import os

import sys
from optparse import OptionParser

from distutils.spawn import find_executable

CSE_STEPS = [""]

ATLAS_MRI_SUFFIX = 'brainsuite.icbm452.lpi.v08a.img'
ATLAS_LABEL_SUFFIX = 'brainsuite.icbm452.v15a.label.img'

BRAINSUITE_ATLAS_DIRECTORY = ""
WORKFLOW_BASE_DIRECTORY = ""
SUBJECT_ID = ""
WORKFLOW_NAME = ""
WORKFLOW_SUFFIX = "_nipype_workflow" #Will be appended to subject ID, to form nipype workflow name. Ex: 1000_nipype
INPUT_MRI_FILE = ""
STATUS_FILEPATH = ""

CURRENT_STATUS = 0
STATUS_NAME = "status.txt"
RUNTIME_EXCEPTION_CODE = -5 #Update statusFile with this code to indicate runtime error during Nipype processing

WORKFLOW_SUCCESS = 0

"""
def updateStatusFile(placeholder):
    Updates file located at STATUS_FILEPATH. This global variable is to be updated in initialization function
    :param placeholder: Placeholder parameter
    :return: Unneeded return value
    global CURRENT_STATUS
    f = open(STATUS_FILEPATH, "w")
    f.write("%d" % CURRENT_STATUS)
    f.close()
    CURRENT_STATUS = CURRENT_STATUS + 1
    return 0

"""

def updateStatusFile(connectFile, secondaryFile, statusPath, status):
    #Checking brainsuite executable path
    from distutils.spawn import find_executable
    import os

    STEP_PNG_SUFFIX = [".png", ".bse.png", ".bfc.png", ".pvc.label.png", ".cerebrum.png", ".init.cortex.png",
                       ".cortex.scrubbed.png", ".cortex.tca.png", ".cortex.dewisp.png", ".inner.cortex.png",
                       ".pial.cortex.png", ".left.png"]

    THUMBNAILS_PATH = os.path.dirname(statusPath) + "/thumbnails/"

    subjectFile = os.path.basename(connectFile)
    subject_id = subjectFile[:subjectFile.index(".")]
    outFile = THUMBNAILS_PATH + subject_id + STEP_PNG_SUFFIX[status]

    DFS_RENDER_OPTIONS = "--zoom 0.5 --xrot -90 --zrot -90 -x 512 -y 512"

    command = ""
    if status <= 8:
        command = ""
        PNG_OPTIONS = "--view 3 --slice 60"
        if status == 1:
            #bse
            command = ("volblend %s -i %s -m %s -o %s" % (PNG_OPTIONS, connectFile, secondaryFile, outFile))
        elif status == 2:
            #bfc
            command = ("volblend %s -i %s -o %s" % (PNG_OPTIONS, connectFile, outFile))
        elif status == 3:
            #pvc

            #NOTE: Change this code when label description xml file changes
            LABEL_DESCRIPTION_FILE = find_executable('bse')[:-3] + '../labeldesc/brainsuite_labeldescriptions_14May2014.xml'
            command = ("volblend %s -i %s -l %s -o %s -x %s" % (PNG_OPTIONS, secondaryFile, connectFile, outFile, LABEL_DESCRIPTION_FILE))
        else:
            command = ("volblend %s -i %s -m %s -o %s" % (PNG_OPTIONS, secondaryFile, connectFile, outFile))




    else:
        #From Pialmesh(step 9) onwards, we are dealing with dfs. Must use dfsrender
        command = ("dfsrender08b_x86_64-redhat-linux-gnu -i %s -o %s %s" % (connectFile, outFile, DFS_RENDER_OPTIONS))

    renderReturnValue = os.system(command)

    print("Saving thumbnail at: %s" % outFile)

    f = open(statusPath, "w")
    f.write("%d" % status)
    f.close()


def init():
    """
    Reads in argument, sets globals to be used in workflow processing
    :return:
    """
    global BRAINSUITE_ATLAS_DIRECTORY
    global WORKFLOW_BASE_DIRECTORY
    global SUBJECT_ID
    global WORKFLOW_NAME
    global INPUT_MRI_FILE
    global STATUS_FILEPATH

    BRAINSUITE_ATLAS_DIRECTORY = find_executable('bse')[:-3] + '../atlas/'

    version_msg = "%prog 1.0"
    usage_msg = """
    %prog DataBaseDirectory
    DataBaseDirectory represents base directory of a subject; should directly contain subjects .nii.gz data
    Example: %prog ~/Documents/webapp/Data/1000
    Expects no trailing slash
    """

    parser = OptionParser(version=version_msg, usage=usage_msg)
    options, args = parser.parse_args(sys.argv[1:])
    if len(args) != 1:
        parser.error("Expected 1 argument, got %s" % len(args))
        return False

    WORKFLOW_BASE_DIRECTORY = os.path.abspath(args[0])
    #TODO: Add auto parsing of a brainsuite settings file, if file exists (this is a possible nice feature)

    SUBJECT_ID = os.path.basename(os.path.normpath(WORKFLOW_BASE_DIRECTORY))
    WORKFLOW_NAME = SUBJECT_ID + WORKFLOW_SUFFIX

    INPUT_MRI_FILE = WORKFLOW_BASE_DIRECTORY + os.sep + SUBJECT_ID + ".nii.gz"
    STATUS_FILEPATH = WORKFLOW_BASE_DIRECTORY + os.sep + STATUS_NAME

def runWorkflow():
    """
    Runs BrainSuite CSE workflow. Globals are to be set during initialization function
    :return:
    """

    #Wrapper function for updating status file. Connect it to all interfaces.
    #updateStatusWrapper = Function(input_names=["placeholder"], output_names=["out"], function=updateStatusFile)
    #updateStatusWrapper.inputs.placeholder = 0


    brainsuite_workflow = pe.Workflow(name=WORKFLOW_NAME)
    brainsuite_workflow.base_dir=WORKFLOW_BASE_DIRECTORY


    bseObj = pe.Node(interface=bs.Bse(), name='BSE')
    bseObj.inputs.inputMRIFile = INPUT_MRI_FILE
    bfcObj = pe.Node(interface=bs.Bfc(),name='BFC')
    pvcObj = pe.Node(interface=bs.Pvc(), name = 'PVC')
    cerebroObj = pe.Node(interface=bs.Cerebro(), name='CEREBRO')
    #Provided atlas files
    cerebroObj.inputs.inputAtlasMRIFile =(BRAINSUITE_ATLAS_DIRECTORY + ATLAS_MRI_SUFFIX)
    cerebroObj.inputs.inputAtlasLabelFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_LABEL_SUFFIX)
    cortexObj = pe.Node(interface=bs.Cortex(), name='CORTEX')
    scrubmaskObj = pe.Node(interface=bs.Scrubmask(), name='SCRUBMASK')
    tcaObj = pe.Node(interface=bs.Tca(), name='TCA')
    dewispObj=pe.Node(interface=bs.Dewisp(), name='DEWISP')
    dfsObj=pe.Node(interface=bs.Dfs(),name='DFS')
    pialmeshObj=pe.Node(interface=bs.Pialmesh(),name='PIALMESH')
    hemisplitObj=pe.Node(interface=bs.Hemisplit(),name='HEMISPLIT')


    #Changes from default settings
    bseObj.inputs.diffusionConstant = 15 #-d
    bseObj.inputs.edgeDetectionConstant = 0.75 #-s

    bfcObj.inputs.histogramType = "ellipse" #--ellipse

    pvcObj.inputs.spatialPrior = 0.1 #-l

    cortexObj.inputs.includeAllSubcorticalAreas = False #turn off the default -a

    #Not changing DFS
    #Not changing pialmesh

    #End changes from default


    bseDoneWrapper = pe.Node(name="BSE_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    bfcDoneWrapper = pe.Node(name="BFC_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    pvcDoneWrapper = pe.Node(name="PVC_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    cerebroDoneWrapper = pe.Node(name="CEREBRO_DONE_WRAPPER",
                                 interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    cortexDoneWrapper = pe.Node(name="CORTEX_DONE_WRAPPER",
                                interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    scrubmaskDoneWrapper = pe.Node(name="SCRUBMASK_DONE_WRAPPER",
                                   interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    tcaDoneWrapper = pe.Node(name="TCA_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    dewispDoneWrapper = pe.Node(name="DEWISP_DONE_WRAPPER",
                                interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    dfsDoneWrapper = pe.Node(name="DFS_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    pialmeshDoneWrapper = pe.Node(name="PIALMESH_DONE_WRAPPER",
                                 interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    hemisplitDoneWrapper = pe.Node(name="HEMISPLIT_DONE_WRAPPER",
                                   interface=Function(input_names=["connectFile", "secondaryFile", "statusPath", "status"], output_names=[],function=updateStatusFile))
    

    bseDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    bfcDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    pvcDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    cerebroDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    cortexDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    scrubmaskDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    tcaDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    dewispDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    dfsDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    pialmeshDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    hemisplitDoneWrapper.inputs.statusPath = STATUS_FILEPATH
    

    bseDoneWrapper.inputs.status = 1
    bfcDoneWrapper.inputs.status = 2
    pvcDoneWrapper.inputs.status = 3
    cerebroDoneWrapper.inputs.status = 4
    cortexDoneWrapper.inputs.status = 5
    scrubmaskDoneWrapper.inputs.status = 6
    tcaDoneWrapper.inputs.status = 7
    dewispDoneWrapper.inputs.status = 8
    dfsDoneWrapper.inputs.status = 9
    pialmeshDoneWrapper.inputs.status = 10
    hemisplitDoneWrapper.inputs.status = 11
    



    #brainsuite_workflow.add_nodes([bseObj, bfcObj, pvcObj, cerebroObj, cortexObj, scrubmaskObj, tcaObj, dewispObj, dfsObj, pialmeshObj, hemisplitObj])

    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bfcObj, 'inputMRIFile')
    #brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bseDoneWrapper, 'connectFile')
    bseDoneWrapper.inputs.connectFile = INPUT_MRI_FILE
    brainsuite_workflow.connect(bseObj, 'outputMaskFile', bseDoneWrapper, 'secondaryFile')

    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcObj, 'inputMRIFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', bfcDoneWrapper, 'connectFile')
    bfcDoneWrapper.inputs.secondaryFile = None

    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', cortexObj, 'inputTissueFractionFile')
    brainsuite_workflow.connect(pvcObj, 'outputLabelFile', pvcDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcDoneWrapper, 'secondaryFile')


    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroObj, 'inputMRIFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cortexObj, 'inputHemisphereLabelFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cerebroDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroDoneWrapper, 'secondaryFile')

    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', scrubmaskObj, 'inputMaskFile')
    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', cortexDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cortexDoneWrapper, 'secondaryFile')

    brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', scrubmaskDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', scrubmaskDoneWrapper, 'secondaryFile')


    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', tcaObj, 'inputMaskFile')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', dewispObj, 'inputMaskFile')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', tcaDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', tcaDoneWrapper, 'secondaryFile')

    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dfsObj, 'inputVolumeFile')
    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dewispDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', dewispDoneWrapper, 'secondaryFile')

    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', pialmeshObj, 'inputSurfaceFile')
    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsDoneWrapper, 'connectFile')
    dfsDoneWrapper.inputs.secondaryFile = None

    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', pialmeshObj, 'inputTissueFractionFile')
    brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', pialmeshObj, 'inputMaskFile')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', hemisplitObj, 'pialSurfaceFile')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', pialmeshDoneWrapper, 'connectFile')
    pialmeshDoneWrapper.inputs.secondaryFile = None

    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', hemisplitObj, 'inputSurfaceFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', hemisplitObj, 'inputHemisphereLabelFile')
    brainsuite_workflow.connect(hemisplitObj, 'outputLeftHemisphere', hemisplitDoneWrapper, 'connectFile')
    hemisplitDoneWrapper.inputs.secondaryFile = None

    brainsuite_workflow.run(plugin='MultiProc', plugin_args={'n_procs': 2})

    #Print message when all processing is complete.
    print('Processing has completed.')

    global WORKFLOW_SUCCESS
    WORKFLOW_SUCCESS = 1




if __name__ == "__main__":
    init()
    runWorkflow()

    if not WORKFLOW_SUCCESS == 1:
        #TODO: update with error code
        exit(1)



    exit(0)
