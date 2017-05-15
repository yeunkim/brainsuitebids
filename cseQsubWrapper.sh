#! /bin/sh

#$ -V
#$ -cwd
#$ -l h_vmem=23G
#$ -l h_rt=11:00:00

#Nodes do not have enough TMP space for Cerebro, so use local temp
#TODO: make this a parameter in subjects.sh (/ifs/tmp/ is specific to this lab)
export TMPDIR=/ifs/tmp/
export TMP=/ifs/tmp/

python `dirname $0`/py/cse.py $1 $2 $3 $4 $5

