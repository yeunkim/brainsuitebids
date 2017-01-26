#! /bin/sh

#$ -V
#$ -cwd

#Nodes do not have enough TMP space for Cerebro, so use local temp
#TODO: make this a parameter in subjects.sh (/ifs/tmp/ is specific to this lab)
export TMPDIR=/ifs/tmp/
export TMP=/ifs/tmp/

python ./py/cse.py $1 $2 $3

