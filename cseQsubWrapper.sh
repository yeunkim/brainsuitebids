#! /bin/sh

#$ -V
#$ -cwd
#$ -l h_vmem=23G
#$ -l h_rt=11:00:00
#$ -N BrainSuite_QC


python $1/py/cse.py $2 $3 $4 $5 $6 $7

