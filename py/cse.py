from __future__ import unicode_literals, print_function
#from builtins import str

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

def updateStatusFile(status):
    f = open(STATUS_FILEPATH, "w")
    f.write("%d" % status)
    f.close()


def bseDone(ph):
    updateStatusFile(1)
def bfcDone(ph):
    updateStatusFile(2)
def pvcDone(ph):
    updateStatusFile(3)
def cerebroDone(ph):
    updateStatusFile(4)
def cortexDone(ph):
    updateStatusFile(5)
def scrubmaskDone(ph):
    updateStatusFile(6)
def tcaDone(ph):
    updateStatusFile(7)
def dewispDone(ph):
    updateStatusFile(8)
def dfsDone(ph):
    updateStatusFile(9)
def pialmeshDone(ph):
    updateStatusFile(10)
def hemisplitDone(ph):
    updateStatusFile(11)

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


    bseDoneWrapper = pe.Node(name="BSE_DONE_WRAPPER",
                             interface=Function(input_names=["ph"], output_names=[],function=bseDone))
    bfcDoneWrapper = pe.Node(name="BFC_DONE_WRAPPER",
                             interface=Function(input_names=["ph"], output_names=[],function=bfcDone))
    pvcDoneWrapper = pe.Node(name="PVC_DONE_WRAPPER",
                             interface=Function(input_names=["ph"], output_names=[],function=pvcDone))
    cerebroDoneWrapper = pe.Node(name="CEREBRO_DONE_WRAPPER",
                                 interface=Function(input_names=["ph"], output_names=[],function=cerebroDone))
    cortexDoneWrapper = pe.Node(name="CORTEX_DONE_WRAPPER",
                                interface=Function(input_names=["ph"], output_names=[],function=cortexDone))
    scrubmaskDoneWrapper = pe.Node(name="SCRUBMASK_DONE_WRAPPER",
                                   interface=Function(input_names=["ph"], output_names=[],function=scrubmaskDone))
    tcaDoneWrapper = pe.Node(name="TCA_DONE_WRAPPER",
                             interface=Function(input_names=["ph"], output_names=[],function=tcaDone))
    dewispDoneWrapper = pe.Node(name="DEWISP_DONE_WRAPPER",
                                interface=Function(input_names=["ph"], output_names=[],function=dewispDone))
    dfsDoneWrapper = pe.Node(name="DFS_DONE_WRAPPER",
                             interface=Function(input_names=["ph"], output_names=[],function=dfsDone))
    pialmeshDonerapper = pe.Node(name="PIALMESH_DONE_WRAPPER",
                                 interface=Function(input_names=["ph"], output_names=[],function=pialmeshDone))
    hemisplitDoneWrapper = pe.Node(name="HEMISPLIT_DONE_WRAPPER",
                                   interface=Function(input_names=["ph"], output_names=[],function=hemisplitDone))


    #brainsuite_workflow.add_nodes([bseObj, bfcObj, pvcObj, cerebroObj, cortexObj, scrubmaskObj, tcaObj, dewispObj, dfsObj, pialmeshObj, hemisplitObj])

    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bfcObj, 'inputMRIFile')
    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bseDoneWrapper, 'ph')

    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcObj, 'inputMRIFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', bfcDoneWrapper, 'ph')


    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', cortexObj, 'inputTissueFractionFile')
    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', pvcDoneWrapper, 'ph')

    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroObj, 'inputMRIFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cortexObj, 'inputHemisphereLabelFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cerebroDoneWrapper, 'ph')

    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', scrubmaskObj, 'inputMaskFile')
    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', cortexDoneWrapper, 'ph')

    brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', scrubmaskDoneWrapper, 'ph')


    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', tcaObj, 'inputMaskFile')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', dewispObj, 'inputMaskFile')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', tcaDoneWrapper, 'ph')

    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dfsObj, 'inputVolumeFile')
    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dewispDoneWrapper, 'ph')

    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', pialmeshObj, 'inputSurfaceFile')
    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsDoneWrapper, 'ph')

    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', pialmeshObj, 'inputTissueFractionFile')
    brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', pialmeshObj, 'inputMaskFile')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', hemisplitObj, 'pialSurfaceFile')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', pialmeshDonerapper, 'ph')


    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', hemisplitObj, 'inputSurfaceFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', hemisplitObj, 'inputHemisphereLabelFile')
    brainsuite_workflow.connect(hemisplitObj, 'outputLeftHemisphere', hemisplitDoneWrapper, 'ph')


    brainsuite_workflow.run()

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
