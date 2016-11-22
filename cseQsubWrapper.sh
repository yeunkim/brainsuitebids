#! /bin/sh

#$ -V
#$ -cwd
#$ -j y
#python ./py/cse.py $1
python qsubTest.py $1

#qsub -V -cwd -o /ifshome/jwong/Documents/qsubTesting/test.log -e /ifshome/jwong/Documents/qsubTesting/test.err.log wrapper.sh 3
