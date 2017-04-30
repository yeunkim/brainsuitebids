# -*- coding: utf-8 -*-
"""
cse.py

Python script to run BrainSuite Cortical Surface Extraction routine
To be called after validating data structure using checks.py

Returns:
    0 on successful processing run
    1 on failure

Usage:
python cse.py T1wFile DerivativeBase public_html

T1wFile is the T1 weighted MRI file for the subject
DerivativeBase is this subject's base directory under the derivatives directory
public_html is the base directory where we may save thumbnails, statistics
Example: %prog ~/Documents/studies/ds225/1003/1003_T1w.nii.gz ~/Documents/studies/ds225/derivatives/1003
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
WORKFLOW_SUFFIX = "_nipype_workflow" #Will be appended to subject ID, to form nipype workflow name.
INPUT_MRI_FILE = ""
INPUT_DWI_BASE = ""
BDP_BASE_DIRECTORY = "DWI"
STATUS_FILEPATH = ""
PUBLIC = ""

CSE_OUTPUTS_DIR="CSE_outputs"

CURRENT_STATUS = 0
STATUSFILE = "status.txt"
RUNTIME_EXCEPTION_CODE = -5 #Update statusFile with this code to indicate runtime error during Nipype processing

WORKFLOW_SUCCESS = 0

def updateStatusFile(connectFile, secondaryFile, statsFiles, statusPath, status, public):
    """
    To be used as a Nipype function interface
    :param connectFile: Should be from an in node to this function call. Ie, should come from the step that we are reporting completion on
    :param secondaryFile: Additional file needed for png rendering calls
    :param statusPath: Path of status file to update
    :param status: Int to be written to file statusPath. Also indicates what stage just finished.
                   Mapping as follows:
                   bse          1
                   bfc          2
                   pvc          3
                   cerebro      4
                   cortex       5
                   scrubmask    6
                   tca          7
                   dewisp       8
                   dfs          9
                   pialmesh     10 
                   hemisplit    11
                   bdp          12
                   svreg        13
    :param public: directory where we may save thumbnails and statistics
    :return: void
    """

    #Checking brainsuite executable path
    from distutils.spawn import find_executable
    import os

    STEP_PNG_SUFFIX = [".png", ".bse.png", ".bfc.png", ".pvc.label.png", ".cerebrum.png", ".init.cortex.png",
                       ".cortex.scrubbed.png", ".cortex.tca.png", ".cortex.dewisp.png", ".inner.cortex.png",
                       ".pial.cortex.png", ".left.png", ".bdp.png", ".svreg.png"]

    STATS_EXECUTABLES = [None, "voxelCount", None, "tissueFrac", None, None, None, None, None, None, None, None, None, None]
    
    STATS_SUFFIX = ["-mri.json", "-bse.json", "-bfc.json", "-pvc.json", "-cerebro.json", "-cortex.json",
                          "-scrubmask.json", "-tca.json", "-dewisp.json", "-dfs.json", "-pialmesh.json",
                          "-hemisplit.json", "-bdp.json", "-svreg.json"]

    subject_id = os.path.basename(os.path.dirname(statusPath))

    #TODO: hardcoded /thumbnails/
    outputPNGFile = public + "/thumbnails/" + subject_id + os.sep + subject_id + STEP_PNG_SUFFIX[status]
    #TODO: hardocded /statistics/
    outputStatsFile = public + "/statistics/" + subject_id + os.sep + subject_id + STATS_SUFFIX[status]

    PNG_OPTIONS = "--view 3 --slice 120"
    DFS_RENDER_OPTIONS = "--zoom 0.5 --xrot -90 --zrot -90 -x 512 -y 512"

    thumbnailCommand = ""
    if status <= 8:
        if status == 1:
            #bse
            thumbnailCommand = ("volblend %s -i %s -m %s -o %s" % (PNG_OPTIONS, connectFile, secondaryFile, outputPNGFile))
        elif status == 2:
            #bfc
            thumbnailCommand = ("volblend %s -i %s -o %s" % (PNG_OPTIONS, connectFile, outputPNGFile))
        elif status == 3:
            #pvc
            #NOTE: Change this code when label description xml file changes
            LABEL_DESCRIPTION_FILE = find_executable('bse')[:-3] + '../labeldesc/brainsuite_labeldescriptions_14May2014.xml'
            thumbnailCommand = ("volblend %s -i %s -l %s -o %s -x %s" % (PNG_OPTIONS, secondaryFile, connectFile, outputPNGFile, LABEL_DESCRIPTION_FILE))
        else:
            thumbnailCommand = ("volblend %s -i %s -m %s -o %s" % (PNG_OPTIONS, secondaryFile, connectFile, outputPNGFile))
    else:
        if status == 12:
            #bdp
            #BDP COMMAND: volblend -i <T1w.nii.gz> -r DWI/<ID>_T1w.dwi.RAS.correct.FA.color.T1_coord.nii.gz -o <outfile> --view 3 --slice 60
            thumbnailCommand = ("volblend %s -i %s -r %s -o %s") % (PNG_OPTIONS, secondaryFile, connectFile, outputPNGFile)
        elif status == 13:
            #svreg
            #SVREG COMMAND: dfsrender -o ~/public_html/test.png -s 2523412.right.pial.cortex.svreg.dfs --zoom 0.5 --xrot -90 --zrot -90 -x 512 -y 512
            thumbnailCommand = ("dfsrender -s %s -o %s %s") % (connectFile, outputPNGFile, DFS_RENDER_OPTIONS)
        else:
            #From Pialmesh(step 9) onwards, we are dealing with dfs. Must use dfsrender
            thumbnailCommand = ("dfsrender -s %s -o %s %s") % (connectFile, outputPNGFile, DFS_RENDER_OPTIONS)

    #TODO: Error check. What behavior if png render failure?
    renderReturnValue = os.system(thumbnailCommand)
    
    stepName = ((STATS_SUFFIX[status]).split("-")[1]).split(".json")[0]
    
    if STATS_EXECUTABLES[status] is not None:
        statsCommand = ("%s -i %s --json >> %s") % (STATS_EXECUTABLES[status], statsFiles, outputStatsFile)
    else:
        tempText = ('{"text": "Statistics currently unavailable for stage %s. Viewing thumbnail generated from %s."}') % (stepName, connectFile)
        statsCommand = ("echo -e '%s' >> %s") % (tempText, outputStatsFile)

    statsReturnValue = os.system(statsCommand)

    print("Saving thumbnail at: %s" % outputPNGFile)

    f = open(statusPath, "w")
    f.write("%d" % status)
    f.close()


def init():
    """
    Reads in argument, sets globals to be used in workflow processing
    :return:
    """
    global INPUT_MRI_FILE
    global INPUT_DWI_BASE
    global BRAINSUITE_ATLAS_DIRECTORY
    global WORKFLOW_BASE_DIRECTORY
    global SUBJECT_ID
    global WORKFLOW_NAME
    global STATUS_FILEPATH
    global PUBLIC
    BRAINSUITE_ATLAS_DIRECTORY = find_executable('bse')[:-3] + '../atlas/'

    version_msg = "%prog 1.0"
    usage_msg = """
    %prog T1wFile DerivativeBase

    T1wFile is the T1 weighted MRI file for the subject
    DerivativeBase is this subject's base directory under the derivatives directory
    Example: %prog ~/Documents/studies/ds225/1003/1003_T1w.nii.gz ~/Documents/studies/ds225/derivatives/1003
    Expecets no trailing slash
    """


    parser = OptionParser(version=version_msg, usage=usage_msg)
    options, args = parser.parse_args(sys.argv[1:])
    if len(args) != 4:
        parser.error("Expected exactly 4 arguments, got %s" % len(args))
        return False
    

    #TODO: Add auto parsing of a brainsuite settings file, if file exists (this is a possible nice feature)
    
    INPUT_MRI_FILE = os.path.abspath(args[0])
    INPUT_DWI_BASE = os.path.abspath(args[1])
    WORKFLOW_BASE_DIRECTORY = os.path.abspath(args[2])
    PUBLIC = os.path.abspath(args[3])

    SUBJECT_ID = os.path.basename(os.path.normpath(WORKFLOW_BASE_DIRECTORY))
    WORKFLOW_NAME = SUBJECT_ID + WORKFLOW_SUFFIX

    STATUS_FILEPATH = WORKFLOW_BASE_DIRECTORY + os.sep + STATUSFILE

def runWorkflow():
    """
    Runs BrainSuite CSE workflow. Globals are to be set during initialization function
    :return:
    """

    brainsuite_workflow = pe.Workflow(name=WORKFLOW_NAME)
    brainsuite_workflow.base_dir=WORKFLOW_BASE_DIRECTORY


    bseObj = pe.Node(interface=bs.Bse(), name='BSE')
    bfcObj = pe.Node(interface=bs.Bfc(),name='BFC')
    pvcObj = pe.Node(interface=bs.Pvc(), name = 'PVC')
    cerebroObj = pe.Node(interface=bs.Cerebro(), name='CEREBRO')
    cortexObj = pe.Node(interface=bs.Cortex(), name='CORTEX')
    scrubmaskObj = pe.Node(interface=bs.Scrubmask(), name='SCRUBMASK')
    tcaObj = pe.Node(interface=bs.Tca(), name='TCA')
    dewispObj=pe.Node(interface=bs.Dewisp(), name='DEWISP')
    dfsObj=pe.Node(interface=bs.Dfs(),name='DFS')
    pialmeshObj=pe.Node(interface=bs.Pialmesh(),name='PIALMESH')
    hemisplitObj=pe.Node(interface=bs.Hemisplit(),name='HEMISPLIT')

    bdpObj = pe.Node(interface=bs.BDP(), name='BDP')
    svregObj = pe.Node(interface=bs.SVReg(), name='SVREG')

    
    #=====Inputs=====
    bdpInputBase = WORKFLOW_BASE_DIRECTORY + os.sep + CSE_OUTPUTS_DIR + os.sep + SUBJECT_ID + '_T1w'
    svregInputBase =  WORKFLOW_BASE_DIRECTORY + os.sep + CSE_OUTPUTS_DIR + os.sep + SUBJECT_ID + '_T1w'

    #Provided input file 
    bseObj.inputs.inputMRIFile = INPUT_MRI_FILE
    #Provided atlas files
    cerebroObj.inputs.inputAtlasMRIFile =(BRAINSUITE_ATLAS_DIRECTORY + ATLAS_MRI_SUFFIX)
    cerebroObj.inputs.inputAtlasLabelFile = (BRAINSUITE_ATLAS_DIRECTORY + ATLAS_LABEL_SUFFIX)
    #bdp inputs that will be created. We delay execution of BDP until all CSE and datasink are done
    bdpObj.inputs.bfcFile = bdpInputBase + '.bfc.nii.gz'
    bdpObj.inputs.inputDiffusionData = INPUT_DWI_BASE + '.nii.gz'
    bdpObj.inputs.BVecBValPair = [ INPUT_DWI_BASE + '.bvec' , INPUT_DWI_BASE + '.bval' ]
    bdpObj.inputs.outputSubdir = BDP_BASE_DIRECTORY
    #svreg inputs that will be created. We delay execution of SVReg until all CSE and datasink are done
    svregObj.inputs.subjectFilePrefix = svregInputBase
       


    #NEW PARAMETERS

    bseObj.inputs.diffusionIterations = 5
    bseObj.inputs.diffusionConstant = 30 #-d
    bseObj.inputs.edgeDetectionConstant = 0.78 #-s

    cerebroObj.inputs.useCentroids = True
    pialmeshObj.inputs.tissueThreshold = 0.3
    #END NEW PARAMETER



    bseDoneWrapper = pe.Node(name="BSE_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    bfcDoneWrapper = pe.Node(name="BFC_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    pvcDoneWrapper = pe.Node(name="PVC_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    cerebroDoneWrapper = pe.Node(name="CEREBRO_DONE_WRAPPER",
                                 interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    cortexDoneWrapper = pe.Node(name="CORTEX_DONE_WRAPPER",
                                interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    scrubmaskDoneWrapper = pe.Node(name="SCRUBMASK_DONE_WRAPPER",
                                   interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    tcaDoneWrapper = pe.Node(name="TCA_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    dewispDoneWrapper = pe.Node(name="DEWISP_DONE_WRAPPER",
                                interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    dfsDoneWrapper = pe.Node(name="DFS_DONE_WRAPPER",
                             interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    pialmeshDoneWrapper = pe.Node(name="PIALMESH_DONE_WRAPPER",
                                 interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    hemisplitDoneWrapper = pe.Node(name="HEMISPLIT_DONE_WRAPPER",
                                   interface=Function(input_names=["connectFile", "secondaryFile", "statsFiles", "statusPath", "status", "public"], output_names=[],function=updateStatusFile))
    

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
    

    bseDoneWrapper.inputs.public = PUBLIC
    bfcDoneWrapper.inputs.public = PUBLIC
    pvcDoneWrapper.inputs.public = PUBLIC
    cerebroDoneWrapper.inputs.public = PUBLIC
    cortexDoneWrapper.inputs.public = PUBLIC
    scrubmaskDoneWrapper.inputs.public = PUBLIC
    tcaDoneWrapper.inputs.public = PUBLIC
    dewispDoneWrapper.inputs.public = PUBLIC
    dfsDoneWrapper.inputs.public = PUBLIC
    pialmeshDoneWrapper.inputs.public = PUBLIC
    hemisplitDoneWrapper.inputs.public = PUBLIC
    
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
    
    


    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bfcObj, 'inputMRIFile')
    bseDoneWrapper.inputs.connectFile = INPUT_MRI_FILE
    brainsuite_workflow.connect(bseObj, 'outputMaskFile', bseDoneWrapper, 'secondaryFile')
    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', bseDoneWrapper, 'statsFiles')
    
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcObj, 'inputMRIFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', bfcDoneWrapper, 'connectFile')
    bfcDoneWrapper.inputs.secondaryFile = None
    bfcDoneWrapper.inputs.statsFiles = None
    
    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', cortexObj, 'inputTissueFractionFile')
    brainsuite_workflow.connect(pvcObj, 'outputLabelFile', pvcDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', pvcDoneWrapper, 'secondaryFile')
    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', pvcDoneWrapper, 'statsFiles')


    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroObj, 'inputMRIFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cortexObj, 'inputHemisphereLabelFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', cerebroDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cerebroDoneWrapper, 'secondaryFile')
    cerebroDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', scrubmaskObj, 'inputMaskFile')
    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', cortexDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', cortexDoneWrapper, 'secondaryFile')
    cortexDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', scrubmaskDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', scrubmaskDoneWrapper, 'secondaryFile')
    scrubmaskDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', tcaObj, 'inputMaskFile')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', dewispObj, 'inputMaskFile')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', tcaDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', tcaDoneWrapper, 'secondaryFile')
    tcaDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dfsObj, 'inputVolumeFile')
    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', dewispDoneWrapper, 'connectFile')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', dewispDoneWrapper, 'secondaryFile')
    dewispDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', pialmeshObj, 'inputSurfaceFile')
    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', dfsDoneWrapper, 'connectFile')
    dfsDoneWrapper.inputs.secondaryFile = None
    dfsDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', pialmeshObj, 'inputTissueFractionFile')
    brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', pialmeshObj, 'inputMaskFile')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', hemisplitObj, 'pialSurfaceFile')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', pialmeshDoneWrapper, 'connectFile')
    pialmeshDoneWrapper.inputs.secondaryFile = None
    pialmeshDoneWrapper.inputs.statsFiles = None

    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', hemisplitObj, 'inputSurfaceFile')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', hemisplitObj, 'inputHemisphereLabelFile')
    brainsuite_workflow.connect(hemisplitObj, 'outputLeftHemisphere', hemisplitDoneWrapper, 'connectFile')
    hemisplitDoneWrapper.inputs.secondaryFile = None
    hemisplitDoneWrapper.inputs.statsFiles = None
    
    ds = pe.Node(io.DataSink(), name='DATASINK')
    ds.inputs.base_directory = WORKFLOW_BASE_DIRECTORY
    
    #**DataSink connections**
    brainsuite_workflow.connect(bseObj, 'outputMRIVolume', ds, CSE_OUTPUTS_DIR)
    brainsuite_workflow.connect(bseObj, 'outputMaskFile', ds, CSE_OUTPUTS_DIR + '.@1')
    brainsuite_workflow.connect(bfcObj, 'outputMRIVolume', ds, CSE_OUTPUTS_DIR + '.@2')
    brainsuite_workflow.connect(pvcObj, 'outputLabelFile', ds, CSE_OUTPUTS_DIR + '.@3')
    brainsuite_workflow.connect(pvcObj, 'outputTissueFractionFile', ds, CSE_OUTPUTS_DIR + '.@4')
    brainsuite_workflow.connect(cerebroObj, 'outputCerebrumMaskFile', ds, CSE_OUTPUTS_DIR + '.@5')
    brainsuite_workflow.connect(cerebroObj, 'outputLabelVolumeFile', ds, CSE_OUTPUTS_DIR + '.@6')
    brainsuite_workflow.connect(cerebroObj, 'outputAffineTransformFile', ds, CSE_OUTPUTS_DIR + '.@7')
    brainsuite_workflow.connect(cerebroObj, 'outputWarpTransformFile', ds, CSE_OUTPUTS_DIR + '.@8')
    brainsuite_workflow.connect(cortexObj, 'outputCerebrumMask', ds, CSE_OUTPUTS_DIR + '.@9')
    brainsuite_workflow.connect(scrubmaskObj, 'outputMaskFile', ds, CSE_OUTPUTS_DIR + '.@10')
    brainsuite_workflow.connect(tcaObj, 'outputMaskFile', ds, CSE_OUTPUTS_DIR + '.@11')
    brainsuite_workflow.connect(dewispObj, 'outputMaskFile', ds, CSE_OUTPUTS_DIR + '.@12')
    brainsuite_workflow.connect(dfsObj, 'outputSurfaceFile', ds, CSE_OUTPUTS_DIR + '.@13')
    brainsuite_workflow.connect(pialmeshObj, 'outputSurfaceFile', ds, CSE_OUTPUTS_DIR + '.@14')
    brainsuite_workflow.connect(hemisplitObj, 'outputLeftHemisphere', ds, CSE_OUTPUTS_DIR + '.@15')
    brainsuite_workflow.connect(hemisplitObj, 'outputRightHemisphere', ds, CSE_OUTPUTS_DIR + '.@16')
    brainsuite_workflow.connect(hemisplitObj, 'outputLeftPialHemisphere', ds, CSE_OUTPUTS_DIR + '.@17')
    brainsuite_workflow.connect(hemisplitObj, 'outputRightPialHemisphere', ds, CSE_OUTPUTS_DIR + '.@18')

    brainsuite_workflow.connect(ds, 'out_file', bdpObj, 'dataSinkDelay')
    brainsuite_workflow.connect(ds, 'out_file', svregObj, 'dataSinkDelay')
    
    brainsuite_workflow.run(plugin='MultiProc', plugin_args={'n_procs': 2})
    
    #bdp command: volblend -i <t1w.nii.gz> -r dwi/<id>_t1w.dwi.ras.correct.fa.color.t1_coord.nii.gz -o <outfile> --view 3 --slice 60
    #SVREG COMMAND: dfsrender -o ~/public_html/test.png -s 2523412.right.pial.cortex.svreg.dfs --zoom 0.5 --xrot -90 --zrot -90 -x 512 -y 512
    updateStatusFile(WORKFLOW_BASE_DIRECTORY + os.sep + CSE_OUTPUTS_DIR + os.sep + BDP_BASE_DIRECTORY + os.sep + SUBJECT_ID + '_T1w.dwi.RAS.correct.FA.color.T1_coord.nii.gz', INPUT_MRI_FILE, None, STATUS_FILEPATH, 12, PUBLIC)
    updateStatusFile(svregInputBase + '.right.pial.cortex.svreg.dfs', None, None, STATUS_FILEPATH, 13, PUBLIC)

    #Print message when all processing is complete.
    print('Processing for subject %s has completed. Nipype workflow is located at: %s' % (SUBJECT_ID, WORKFLOW_BASE_DIRECTORY))

    global WORKFLOW_SUCCESS
    WORKFLOW_SUCCESS = 1


if __name__ == "__main__":
    init()
    runWorkflow()

    if not WORKFLOW_SUCCESS == 1:
        #TODO: update with error code
        exit(1)

    exit(0)
