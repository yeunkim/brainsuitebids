#! /bin/sh

USAGE_MESSAGE="Usage: `basename $0` dataset public_html\n\tdataset must be the path to a BIDS formatted dataset.\n\tpublic_html is directory where index.html, thumbnails directory, and brainsuite_state.json will be created. Will create directory if does not already exist\n"

echo
echo "BrainSuite QC System"
echo

if [ "$#" -ne 2 ]
then
    echo -e ${USAGE_MESSAGE}
    echo "Error: Expected exactly 2 command line arguments, got $#"
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

if [ ! -d $2 ]
then
    mkdir $2
    if [ $? -ne 0 ]
    then
        echo -e ${USAGE_MESSAGE}
        echo "Error creating directory $2"
        echo "Exiting with error code 1"
        exit 1
    fi

    echo "Created directory $2"
else
    if [ ! -r $2 ]
    then
        echo "Error. Lacking read permissions on directory $2"
        echo "Exiting with error code 1"
        exit 1
    fi

    if [ ! -w $2 ]
    then
        echo "Error. Lacking write permissions on directory $2"
        echo "Exiting with error code 1"
        exit 1
    fi
    
    if [ ! -x $2 ]
    then
        echo "Error. Lacking execute permissions on directory $2"
        echo "Exiting with error code 1"
        exit 1
    fi

    echo "Will be using existing directory $2"
fi


PARTICIPANTS_FILE=$1/participants.tsv
DERIVATIVES_DIR=$1/Derivatives
THUMBNAILS_PATH="/thumbnails"
STATUS_FILENAME="/status.txt"
LOG_PATH="/logging"
BASE_DIRECTORY=""
PNG_OPTIONS="--view 3 --slice 60"

if [ ! -e $PARTICIPANTS_FILE ]
then
    echo -e ${USAGE_MESSAGE}
    echo "Error: $1/participants.tsv does not exist."
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

readingHeader=1
participantIndex=-1
OLD_IFS=$IFS
IFS=$'\n'
for line in `grep -v "^[[:space:]]*$" $PARTICIPANTS_FILE`
do
    if [ ${readingHeader} -eq 1 ]
    then
        mkdir -p ${1}${LOG_PATH}
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
        mkdir -p ${subjectDerivativeBase}
        mkdir -p ${subjectDerivativeBase}${THUMBNAILS_PATH}
        volblend ${PNG_OPTIONS} -i ${subjectDataFile} -o ${subjectDerivativeBase}${THUMBNAILS_PATH}/${subjID}.png
        echo -1 > ${subjectDerivativeBase}${STATUS_FILENAME}
        logFile=${DERIVATIVES_DIR}${LOG_PATH}/${subjID}.log
        logErrFile=${DERIVATIVES_DIR}${LOG_PATH}/${subjID}.err.log
        qsub -o $logFile -e $logErrFile cseQsubWrapper.sh ${subjectBase} ${subjectDerivativeBase} $2
    fi
done

IFS=$OLD_IFS
python ./py/genStatusFile.py $1 $2

exit 0

