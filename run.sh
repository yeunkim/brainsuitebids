#! /bin/sh

USAGE_MESSAGE="Usage: `basename $0` DataStructureFile\n\n\
Expected format of DataStructureFile:\n\
Path to Data directory (absolute path, no trailing slash)\n\
\tSubject_dir_1 (No trailing or leading slash)\n\
\t...\n\
\tSubject_dir_n"

if [ "$#" -ne 1 ]
then
    echo ${USAGE_MESSAGE}
    echo "Error. Expected exactly 1 command line argument, got $#"
    echo "Exiting with error code 1"
    exit 1
fi

python ./py/checks.py $1
if [ $? -ne 0 ]
then
    echo "Error. Checks.py failure."
    echo "Exiting with error code 2"
    exit 2
fi
#If checks.py passed, we know input file is well formatted, and is not empty


THUMBNAILS_PATH="/thumbnails"
STATUS_FILENAME="/status.txt"
LOG_PATH="/logging"
BASE_DIRECTORY=""
PNG_OPTIONS="--view 3 --slice 60"
for line in `grep -v "^[[:space:]]*$" $1`
do
    if [ -z ${BASE_DIRECTORY} ]
    then
        BASE_DIRECTORY=${line}
        mkdir -p ${BASE_DIRECTORY}${LOG_PATH}
    else
        subjectBase=${BASE_DIRECTORY}/${line}
        #echo ${subjectBase}${THUMBNAILS_PATH}/${line}.png
        mkdir -p ${subjectBase}${THUMBNAILS_PATH}
        volblend $PNG_OPTIONS -i ${subjectBase}/${line}.nii.gz -o ${subjectBase}${THUMBNAILS_PATH}/${line}.png
        echo -1 > ${subjectBase}${STATUS_FILENAME}
        logFile=${BASE_DIRECTORY}${LOG_PATH}/${line}.log
        logErrFile=${BASE_DIRECTORY}${LOG_PATH}/${line}.err.log
        qsub -o $logFile -e $logErrFile cseQsubWrapper.sh ${subjectBase}
    fi
done



python ./py/genStatusFile.py $1

exit 0

