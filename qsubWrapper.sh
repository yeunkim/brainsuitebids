#! /bin/sh

#$ -V
#$ -cwd
#$ -l h_vmem=23G
#$ -l h_rt=11:00:00
#$ -N BrainSuite_QC

if [ ! -z $8 ]
then
    #newTemp. Used if compute nodes dont have enough tmp memory, or tmp dir is full
    export TMPDIR="$8"
    export TMP="$8"
fi

python $1/py/brainsuiteWorkflow.py $2 $3 $4 $5 $6 $7

