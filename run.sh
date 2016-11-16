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
        #echo "AAA" > ${BASE_DIRECTORY}${LOG_PATH}/${line}.log
    fi
done

exit 1

python ./py/checks.py $1
if [ $? -ne 0 ]
then
    echo "Error. Checks.py failure."
    echo "Exiting with error code 2"
    exit 2
fi

#If checks.py passed, we know input file is well formatted, and is not empty
#qsub -S $(which python) -o /ifshome/jwong/Documents/qsubTesting/newFolder/test.log -e /ifshome/jwong/Documents/qsubTesting/newFolder/test.err.log test.py 123
#volblend -i 1003.nii.gz --view 3 -o test.png