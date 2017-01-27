#! /bin/sh

USAGE_MESSAGE=\
"\n\n
Usage: `basename $0` dataset [public]\n
\tdataset\n
\t\tmust be the path to a BIDS formatted dataset. participants.tsv is required for this program to work\n
\tpublic\n
\t\tdirectory where index.html, thumbnails directory, and brainsuite_state.json will be created.\n
\t\tProgram will create public directory if it does not already exist\n
\t\tIf public is unspecified, its value will default to dataset/Derivatives 
\n
Additional info:\n
To view QC system on browser, navigate to public directory in web browser.\n
(Ideally, public would be a public_html directory, or a directory made public through a webserver)\n
\n
All derived data will be placed in the Derivatives directory, as described by BIDS specifications\n
Each subject's derived folder will contain the nipype_workflow; intermediate data from each step can be found here\n

\n\n
"

echo
echo "BrainSuite QC System"
echo

if [ "$#" -ne 2 ] && [ "$#" -ne 1 ]
then
    echo -e ${USAGE_MESSAGE}
    echo "Error: Expected 1 or 2 command line arguments, got $#"
    echo "Exiting with error code 1"
    exit 1
fi

PARTICIPANTS_FILE=$1/participants.tsv
DERIVATIVES_DIR=$1/Derivatives
mkdir -p ${DERIVATIVES_DIR}
THUMBNAILS_PATH="/thumbnails"
STATUS_FILENAME="/status.txt"
LOG_PATH="/logging"
BASE_DIRECTORY=""
PNG_OPTIONS="--view 3 --slice 60"
PUBLIC=""
if [ "$#" -eq 1 ]
then
    PUBLIC=DERIVATIVES_DIR
    echo "no public directory was specified; will save web files in $PUBLIC"
else
    PUBLIC=$2
fi

if [ ! -e $PARTICIPANTS_FILE ]
then
    echo -e ${USAGE_MESSAGE}
    echo "Error: $PARTICIPANTS_FILE does not exist."
    echo "Exiting with error code 1"
    exit 1
fi

if [ ! -d $1 ]
then
    echo -e ${USAGE_MESSAGE}
    echo "Error: $1 is not a directory."
    echo "Exiting with error code 1"
    exit 1
fi

python ./py/checks.py $PARTICIPANTS_FILE
if [ $? -ne 0 ]
then
    echo "Error. Checks.py failure."
    echo "Exiting with error code 2"
    exit 2
fi
#If checks.py passed, we know BIDS dataset is well formatted

#Check existance of PUBLIC directory, create if needed.
if [ ! -d ${PUBLIC} ]
then
    mkdir ${PUBLIC}
    if [ $? -ne 0 ]
    then
        echo -e ${USAGE_MESSAGE}
        echo "Error creating directory ${PUBLIC}"
        echo "Exiting with error code 1"
        exit 1
    fi

    echo "Created directory ${PUBLIC}"
else
    if [ ! -r ${PUBLIC} ] || [ ! -w ${PUBLIC} ] || [ ! -x ${PUBLIC} ]
    then
        echo "Error. Lacking read permissions on directory ${PUBLIC}"
        echo "Exiting with error code 1"
        exit 1
    fi
    
    echo "Will be using existing directory ${PUBLIC}"
fi


#Parse subjects from PARTICIPANTS_FILE, make qsub calls
readingHeader=1
participantIndex=-1
OLD_IFS=$IFS
IFS=$'\n'
for line in `grep -v "^[[:space:]]*$" $PARTICIPANTS_FILE`
do
    if [ ${readingHeader} -eq 1 ]
    then
        mkdir -p ${DERIVATIVES_DIR}${LOG_PATH}
        IFS=$'\t ' read -r -a header <<< ${line}
        for i in "${!header[@]}"
        do
            if [ ${header[$i]} = "participant_id" ]
            then
                participantIndex=$i
            fi
        done

        readingHeader=0
    else
        IFS=$'\t '
        read -r -a row <<< ${line}
        subjID=${row[$participantIndex]}
        subjectDataFile=${1}/${subjID}/anat/${subjID}_T1w.nii.gz
        subjectDerivativeBase=${DERIVATIVES_DIR}/${subjID}
        subjectThumbnailsBase=${PUBLIC}/${THUMBNAILS_PATH}/${subjID}

        mkdir -p ${subjectDerivativeBase}
        mkdir -p ${subjectThumbnailsBase}
        volblend ${PNG_OPTIONS} -i ${subjectDataFile} -o ${subjectThumbnailsBase}/${subjID}.png
        echo -1 > ${subjectDerivativeBase}${STATUS_FILENAME}
        logFile=${DERIVATIVES_DIR}${LOG_PATH}/${subjID}.log
        logErrFile=${DERIVATIVES_DIR}${LOG_PATH}/${subjID}.err.log
        qsub -o $logFile -e $logErrFile cseQsubWrapper.sh ${subjectDataFile} ${subjectDerivativeBase} ${PUBLIC}
    fi
done

IFS=$OLD_IFS
cp index.html ${PUBLIC}
python ./py/genStatusFile.py $PARTICIPANTS_FILE ${PUBLIC}

exit 0

