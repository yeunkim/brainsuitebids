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
LOG_PATH="/logging"
BASE_DIRECTORY=""
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
        volblend -i ${subjectBase}/${line}.nii.gz --view 3 -o ${subjectBase}${THUMBNAILS_PATH}/${line}.png
        logFile=${BASE_DIRECTORY}${LOG_PATH}/${line}.log
        logErrFile=${BASE_DIRECTORY}${LOG_PATH}/${line}.err.log
        #qsub -V -cwd -o /ifshome/jwong/Documents/qsubTesting/test.log -e /ifshome/jwong/Documents/qsubTesting/test.err.log wrapper.sh 3
        #echo "AAA" > ${BASE_DIRECTORY}${LOG_PATH}/${line}.log
        #./cseWrapper.sh ${subjectBase}
        qsub cseQsubWrapper.sh ${subjectBase}
    fi
done

python ./py/genStatusFile.py $1

exit 0

#qsub -V -cwd -o /ifshome/jwong/Documents/qsubTesting/test.log -e /ifshome/jwong/Documents/qsubTesting/test.err.log wrapper.sh 3