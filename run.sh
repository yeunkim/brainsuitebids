#! /bin/bash

show_help(){
cat << EOF
BrainSuite QC System

Usage: `basename $0` -d <directory_path> [settings]

Required positional arguments:
-d <directory_path>         
    path to a BIDS formatted dataset. participants.tsv is required for
    this program to work. Program will determine what subjects to process
    using the contents of participants.tsv. You may edit participants.tsv
    to ignore subjects in the dataset. You may then use -i <regex> and
    -s <regex> to filter by subject ID and session.

Optional settings:
-p <directory_path>
    directory where index.html, thumbnails directory, and
    brainsuite_state.json will be created. Program will create public
    directory if it does not already exist.
    [default: <dataset>/derivatives, where <dataset> is input to -d]

-w
    set up a basic web server to serve files from public directory.
    web server defaults to port 8080, increments port number if
    if 8080 is unavailable, until available port is found.

-r <processing_steps>
    Controls what processing will be done in addition to CSE.
    If BDP is enabled, will first check for dwi data; if dwi data is
    not found, BDP will be disabled.
    <processing_steps> must be one of: {bdp, svreg, none, all} ##TODO: change none to cse and add more stages
    [default: all]

-i <regex>
    provide a regex to filter subjects by subjectID. Only subjects whose 
    subject ID match the provided regex will be processed.
    Expression will be interpreted in ERE syntax; will act like grep -E
    on each subject name in your dataset. Quotes around your expression
    are not required, but are recommended when using special operators
    such as or (|).
    Can be used along with -s <regex>.
    [default: .*]

-s <regex>
    provide a regex to filter by session label. If dataset does not
    include session layer of directory structure (this is only allowed by
    BIDS when each subject has exactly one session), then session label
    regex will be ignored. Only data from sessions whose session label
    match the provided regex will be processed.
    Expression will be interpreted in ERE syntax; will act like grep -E
    on each session label in your dataset. Quotes around your expression
    are not required, but are recommended when using special operators
    such as or (|).
    Can be used along with -i <regex>.
    [default: .*]

-t <tmpdir> (remove?)
    change the TMP and TMPDIR shell variables to <tmpdir> when
    submitting job to qsub. Should be used if compute nodes
    lack tmp space, or if tmp directories are full. <tmpdir> 
    should be a directory for which you have permissions.

-x
    For testing purposes. Will cause program to print out name of
    each file that would have been processed, without actually 
    starting any processing jobs.
    Useful for debugging or for testing your regex matches.

-l
    do all processing locally, without using qsub. Will automatically
    activate this option if qsub can not be found in your path.

Additional information:
======================
To view QC system on browser, navigate to public directory in web browser.
(Ideally, public would be a public_html directory, or a directory made
public through a webserver).

All derived data will be placed in the derivatives directory, as required
by BIDS specifications.

All thumbnails and statistical reports will be placed in public directory

EOF
}


initAndProcess () {
    id=$1 #id and possibly ses
    dataFile=$2
    dwiBase=$3
    demographics=$4

    echo "==========${id}=========="

    svreg=${a_r_svreg}
    bdp=${a_r_bdp}

    if [ ${bdp} -eq 1 ]
    then
        dwiPrefixes=( '.bval' '.bvec' '.nii.gz' )
        for prefix in "${dwiPrefixes[@]}"
        do
            if [ ! -e ${dwiBase}${prefix} ]
            then
                echo "File ${dwiBase}${prefix} does not exist. Turned BDP off"
                bdp=0
                break
            fi
        done
        
    fi

    willProcess="CSE"
    if [ ${bdp} -eq 1 ]
    then
        willProcess="${willProcess} BDP"
    fi

    if [ ${svreg} -eq 1 ]
    then
        willProcess="${willProcess} SVReg"
    fi

    echo "Processing will perform: ${willProcess}"

    if [ ! -e ${dataFile} ]
    then
        echo "Error: file ${dataFile} does not exist. Skipping this subject."
        echo "=========================================="
        echo ""
        return 
    fi

    if [ ${a_x} -eq 1 ]
    then
        echo "${dataFile}"
        echo "=========================================="
        echo ""
        return 0
    fi

    echo ${id} >> "${subjectsAndSessionsFile}"

    subjectDerivativeBase=${DERIVATIVES_DIR}/${id}
    subjectThumbnailsBase=${PUBLIC}/${THUMBNAILS_PATH}/${id}
    subjectStatsBase=${PUBLIC}/${STATS_PATH}/${id}

    mkdir -p ${subjectDerivativeBase}
    cp ${dataFile} ${subjectDerivativeBase}

    mkdir -p ${subjectThumbnailsBase}
    volblend ${PNG_OPTIONS} -i ${dataFile} -o ${subjectThumbnailsBase}/${id}.png
    
    mkdir -p ${subjectStatsBase}
    echo -e "{\"text\": \"Viewing input MRI data, filename ${dataFile}\"}" > ${subjectStatsBase}/${id}-mri.json
    echo $demographics > ${subjectStatsBase}/${id}_demographics.txt

    echo -1 > ${subjectDerivativeBase}${STATUS_FILENAME}
    logFile=${DERIVATIVES_DIR}${LOG_PATH}/${id}.log
    logErrFile=${DERIVATIVES_DIR}${LOG_PATH}/${id}.err.log

    ## TODO: turn off qsub functions?
    if [ $noQsub -eq 0 ]
    then
        qsub -o $logFile -e $logErrFile `dirname $0`/qsubWrapper.sh `dirname $0` "${dataFile}" "${dwiBase}" "${subjectDerivativeBase}" "${PUBLIC}" "${bdp}" "${svreg}" "${newTemp}"
    else
        echo "Registered local background process for file: ${dataFile}"
        `dirname $0`/qsubWrapper.sh `dirname $0` "${dataFile}" "${dwiBase}" "${subjectDerivativeBase}" "${PUBLIC}" "${bdp}" "${svreg}" "${newTemp}" > $logFile 2> $logErrFile &
    fi

    echo "=========================================="
    echo ""
}

check_duplicate_option(){
    if [ $1 -eq 1 ]
    then
        echo "Option $2 provided twice. Incorrect usage. Exiting."
        echo "For usage instructions, call `basename $0` with no options"
        return 1
    fi
}

killWebServer(){
    if [ $a_w -eq 1 ]
    then
        kill $webserverPID
        echo ""
        echo "Webserver has been shut down. To restart it, run:"
        echo "python $(readlink -f `dirname $0`)/py/webserver.py ${PUBLIC}"
        echo ""
    fi
}

awkLine(){
    awkIndex=`echo "$1" | awk -F $'\t' -v searchFor=$2 '
    {
        for(i=1;i<=NF;i++){
            if($i == searchFor){
                print i;
                exit 0;
            }
        }
        exit 1
    }'`
}
awkCheckColCountAndHeader(){
    cat $PARTICIPANTS_FILE | sed 's/\r$//g' | sed 's/\r/\n/g' | awk -F $'\t' '
    BEGIN{
        starting=0
        headerNF=-1
        foundError=0
        participantCol=-1
    }
    {
        if(starting == 0){
            starting=1;
            headerNF=NF;

            foundParticipantEntry=0;
            
            #Check that header has participant_id column
            for(i=1;i<=NF;i++){
                if(tolower($i) == "participant_id"){
                    foundParticipantEntry=1;
                    participantCol=i
                }
            }

            if(foundParticipantEntry == 0){
                print "Error in participants.tsv file. Header row does not contain a participant_id column";
                foundError=1;
                exit;
            }
        }else{
            if(NF != headerNF){
                printf("Error: participants.tsv header has %d columns, but row %d has %d columns. Col count must be equal.\n", headerNF, NR, NF);
                foundError=1;
                exit;
            }

            if(length($participantCol) == 0){
                printf("Error: participant_id column in row %d is empty.\n", NR);
                foundError=1;
                exit;
            }
        }
    }
    END{
        if(foundError == 0){
            exit 0;
        }else{
            exit 1;
        }
    }
    '
}

#1: line to awk. 2: col to print. Will echo the col
awkGetCol(){
    echo "$1" | awk -F $'\t' -v colToPrint="$2" '{print $colToPrint}'
}

#Check execuatble in path. **Will exit script if not.**
checkExecutable(){
    command -v "$1" > /dev/null 2>&1
    if [ $? -ne 0 ]
    then
        echo "ERROR: Executable $1 required, but not found in system path. Exiting."
        exit 1
    fi
}


#Check brainsuite atlas dir exist. Assume bse in path, so call after checking BSE in path
checkAtlasDir(){
    local brainsuiteBin=`command -v bse`
    brainsuiteBin=`dirname "$brainsuiteBin"`
    local atlasDir="$brainsuiteBin"/../atlas/
    if [ ! -d "$atlasDir" ]
    then
        echo "ERROR: BrainSuite atlas directory does not exist. Exiting. It should be at: ${atlasDir}"
        exit 1
    fi
}


THUMBNAILS_PATH="/thumbnails"
STATS_PATH="/statistics"
STATUS_FILENAME="/status.txt"
LOG_PATH="/logging"
BASE_DIRECTORY=""
PNG_OPTIONS="--view 3 --slice 120"
PUBLIC=""

ARG_DATASET="" #set in optparse
PARTICIPANTS_FILE="" #set in optparse
DERIVATIVES_DIR="" #set in optparse
SUBJECT_REGEX=".*" #set in optparse
SESSION_REGEX=".*" #set in optparse

OPTIND=1
gotOption=0

a_gotOption=0
a_d=0
a_p=0
a_w=0

a_r_svreg=1 #Default on
a_r_bdp=1 #Default on

a_i=0
a_s=0
a_x=0
newTemp="" #If remains "" when passed to qsubWrapper, then qsubWrapper will take no action
webserverPID=-1
noQsub=0


while getopts ":d:p:wr:i:s:xt:l" opt; do
    a_gotOption=1
    case $opt in
        \?)
            echo "Invalid option: -$OPTARG" >&2
            echo "For usage instructions, call `basename $0` with no options"
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            echo "For usage instructions, call `basename $0` with no options"
            exit 1
            ;;
        d)
            check_duplicate_option $a_d $opt
            if [ $? -ne 0 ]; then exit 1; fi
            a_d=1
            PARTICIPANTS_FILE=$OPTARG/participants.tsv
            DERIVATIVES_DIR=$OPTARG/derivatives
            ARG_DATASET=$OPTARG
            ;;
        p)
            check_duplicate_option $a_p $opt
            if [ $? -ne 0 ]; then exit 1; fi
            a_p=1
            PUBLIC=$OPTARG
            ;;
        w)
            a_w=1
            ;;
        r)
            a_r_tolower=`echo $OPTARG | tr '[:upper:]' '[:lower:]'`

            if [ ${a_r_tolower} == "bdp" ]
            then
                a_r_svreg=0
                a_r_bdp=1
            elif [ ${a_r_tolower} == "svreg" ]
            then
                a_r_svreg=1
                a_r_bdp=0
            elif [ ${a_r_tolower} == "none" ]
            then
                a_r_svreg=0
                a_r_bdp=0
            elif [ ${a_r_tolower} == "all" ]
            then
                a_r_svreg=1
                a_r_bdp=1
            else
                echo "Usage Error: Argument to -r must be one of: {bdp, svreg, none, all}" 
                exit 1
            fi
            ;;
        i)
            check_duplicate_option $a_i $opt
            if [ $? -ne 0 ]; then exit 1; fi
            a_i=1
            SUBJECT_REGEX=$OPTARG
            ;;
        s)
            check_duplicate_option $a_s $opt
            if [ $? -ne 0 ]; then exit 1; fi
            a_s=1
            SESSION_REGEX=$OPTARG
            ;;
        x)
            a_x=1
            ;;
        t)
            newTemp="$OPTARG"
            ;;
        l)
            noQsub=1
            ;;
    esac
done

shift $((OPTIND-1))

if [ $# -ne 0 ]
then
    echo Unrecognized option $1
    echo "For usage instructions, call `basename $0` with no options"
    exit 1
fi

if [ $a_gotOption -eq 0 ]
then
    show_help
    exit 1
fi

if [ $a_d -eq 0 ]
then
    echo "Option -d is mandatory, but was not provided."
    echo "For usage instructions, call `basename $0` with no options"
    exit 1
fi

if [ $noQsub -eq 1 ]
then
    echo "-l option was used. Will process jobs locally"
else
    echo "Checking for qsub in PATH"
    command -v qsub > /dev/null 2>&1
    if [ $? -ne 0 ]
    then
        echo "-l option was not used, but qsub was not found in PATH. Will process jobs locally"
        noQsub=1
    else
        echo "qsub found in PATH, will submit processing jobs using qsub"
    fi
fi

#Done parsing arguments


#Checks:

#Participants file exists
if [ ! -e $PARTICIPANTS_FILE ]
then
    echo "Error: $PARTICIPANTS_FILE does not exist."
    echo "For usage instructions, call `basename $0` with no options"
    exit 1
fi

#Dataset exists
if [ ! -d $ARG_DATASET ]
then
    echo "Error: Dataset directory $ARG_DATASET does not exist."
    echo "For usage instructions, call `basename $0` with no options"
    exit 1
fi


#executables in path:
checkExecutable "bse"
checkExecutable "svreg.sh"
checkExecutable "bdp.sh"
checkExecutable "voxelCount"
checkExecutable "tissueFrac"
checkExecutable "python"

checkAtlasDir

#Nipype and BrainSuite Nipype interface import checks
python `dirname $0`/py/checkNipypeInstallation.py
if [ $? -ne 0 ]
then
    exit 1
fi

#Check existance of PUBLIC directory, create if needed.
if [ $a_p -eq 0 ]
then
    PUBLIC=$DERIVATIVES_DIR
    echo "Public Directory: No public directory was specified using -p. Will save web files in $PUBLIC"
fi
if [ ! -d ${PUBLIC} ]
then
    mkdir -p ${PUBLIC}
    if [ $? -ne 0 ]
    then
        echo "Error creating directory ${PUBLIC}"
        echo "For usage instructions, call `basename $0` with no options"
        exit 1
    fi

    echo "Public Directory: Created directory to be used for public files: ${PUBLIC}"
else
    if [ ! -r ${PUBLIC} ] || [ ! -w ${PUBLIC} ] || [ ! -x ${PUBLIC} ]
    then
        echo "Error. Lacking permissions on directory ${PUBLIC}. Exiting."
        exit 1
    fi
    
    echo "Public Directory: Will be using the existing directory ${PUBLIC}"
fi

#participants.tsv
awkCheckColCountAndHeader
if [ $? -ne 0 ]
then
    exit 1
fi

#All checks done

echo ""
echo "===Looping through participants.tsv and submitting processing jobs==="
echo ""

#Parse subjects from PARTICIPANTS_FILE, make qsub calls
readingHeader=1
participantIndex=-1
ageIndex=-1 #-1: no age provided. else will be col index
sexIndex=-1 #-1: no sex provided. else will be col index
isMultiSession=-1 #-1:undetermined; 1:is multisession 0:not multisession.
subjectsAndSessionsFile=""

#Used process substitution to loop over participants tsv file
while read line
do

    if [ ${readingHeader} -eq 1 ]
    then
        line=`echo "${line}" | tr '[:upper:]' '[:lower:]'`

        awkIndex=0

        awkLine "$line" "participant_id"
        if [ $? -eq 0 ]
        then
            participantIndex="$awkIndex"
        fi

        awkLine "$line" "age"
        if [ $? -eq 0 ]
        then
            ageIndex="$awkIndex"
        fi

        awkLine "$line" "sex"
        if [ $? -eq 0 ]
        then
            sexIndex="$awkIndex"
        fi

        mkdir -p "${DERIVATIVES_DIR}""${LOG_PATH}"
        subjectsAndSessionsFile=${DERIVATIVES_DIR}/subjAndSes-`date +%Y%m%d-%H%M%S`-$$.txt
        touch ${subjectsAndSessionsFile}
        readingHeader=0
    else
        subjID=`awkGetCol "$line" "$participantIndex"`
        subjDemographics=""

        subjAge=""
        subjSex=""
        if [ $ageIndex -ne -1 ]
        then
            subjAge=`awkGetCol "$line" "$ageIndex"`
            if [ ! -z "$subjAge" ]
            then
                #TODO handle not a number
                subjAge="$(((${subjAge%.*} / 10) * 10))" #Floor to 10's place
            fi
        fi

        if [ $sexIndex -ne -1 ]
        then
            subjSex=`awkGetCol "$line" "$sexIndex"`
            if [ ! -z "$subjSex" ]
            then
                subjSex=`echo "$subjSex" | tr '[:upper:]' '[:lower:]'`
                subjSex=${subjSex:0:1} #First letter only
            fi
        fi

        subjDemographics="$subjAge""$subjSex"
        if [ -z "$subjDemographics" ]
        then
            subjDemographics="all"
        fi


        if [ ! -d ${ARG_DATASET}/${subjID} ]
        then
            echo "==========${subjID}=========="
            echo "Directory ${ARG_DATASET}/${subjID} does not exist. Skipping this subject"
            echo "=========================================="
            continue
        fi
        
        if [ $isMultiSession -eq -1 ]
        then
            #If subject directory contains folder containing ses-
            if [[ $(ls ${ARG_DATASET}/${subjID} | grep "ses-") ]]
            then
                isMultiSession=1
            else
                isMultiSession=0
            fi
        fi
        
        if [[ ${subjID} =~ ${SUBJECT_REGEX} ]]
        then
            if [ ${isMultiSession} -eq 1 ]
            then
                #Process redirection
                while read s
                do
                    if [ -d ${ARG_DATASET}/${subjID}/${s} ] && [[ ${s} =~ ${SESSION_REGEX} ]]
                    then
                        subjAndSesID=${subjID}_${s}
                        subjectDataFile=${ARG_DATASET}/${subjID}/${s}/anat/${subjAndSesID}_T1w.nii.gz
                        subjectDwiBase=${ARG_DATASET}/${subjID}/${s}/dwi/${subjAndSesID}_dwi

                        initAndProcess ${subjAndSesID} ${subjectDataFile} ${subjectDwiBase} ${subjDemographics}
                    fi
                done < <(ls ${ARG_DATASET}/${subjID})
            else
                subjectDataFile=${ARG_DATASET}/${subjID}/anat/${subjID}_T1w.nii.gz
                subjectDwiBase=${ARG_DATASET}/${subjID}/dwi/${subjID}_dwi

                initAndProcess ${subjID} ${subjectDataFile} ${subjectDwiBase} ${subjDemographics}
            fi
        fi
    fi
    
done < <(cat $PARTICIPANTS_FILE | sed 's/\r$//g' | sed 's/\r/\n/g')
#Sed is for DOS support

if [ $a_x -eq 1 ]
then
    exit 0
fi


if [ $a_w -eq 1 ]
then
    trap killWebServer EXIT
    echo ""
    echo "Registering background process for webserver."
    echo "Webserver will be closed when this script stops running"
    echo "To restart webserver manually at a later time, run:"
    echo "python $(readlink -f `dirname $0`)/py/webserver.py ${PUBLIC}"
    echo ""

    python `dirname $0`/py/webserver.py ${PUBLIC} 2> /dev/null &
    webserverPID=$!
fi


cp `dirname $0`/NA.png ${PUBLIC}/${THUMBNAILS_PATH}
cp `dirname $0`/index.html ${PUBLIC}
cp `dirname $0`/icbm100_statistics.json ${PUBLIC}/statistics_base.json #TODO hardcoded
python `dirname $0`/py/genStatusFile.py ${subjectsAndSessionsFile} ${PUBLIC}

exit 0

