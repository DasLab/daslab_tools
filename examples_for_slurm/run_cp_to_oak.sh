#!/bin/bash
#SBATCH --job-name=cp_fastq
#SBATCH --output=cp_fastq.out
#SBATCH --error=cp_fastq.err
#SBATCH --partition=biochem
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

DIRNAME=OK45_Test2
cp -r  usftp21.novogene.com/01.RawData/$DIRNAME  /oak/stanford/groups/rhiju/sherlock/scratch/rhiju/Novogene/
md5sum  /oak/stanford/groups/rhiju/sherlock/scratch/rhiju/Novogene/${DIRNAME}/*gz
cat  /oak/stanford/groups/rhiju/sherlock/scratch/rhiju/Novogene/${DIRNAME}/MD5.txt
echo "DONE"
