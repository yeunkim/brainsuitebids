#! /bin/sh

#$ -V
#$ -cwd
#$ -j y

#Nodes do not have enough TMP space for Cerebro, so use local temp
#TODO: make this a parameter in subjects.sh (/ifs/tmp/ is specific to this lab)
export TMPDIR=/ifs/tmp/
export TMP=/ifs/tmp/

python ./py/cse.py $1

#qsub -V -cwd -o /ifshome/jwong/Documents/qsubTesting/test.log -e /ifshome/jwong/Documents/qsubTesting/test.err.log wrapper.sh 3
