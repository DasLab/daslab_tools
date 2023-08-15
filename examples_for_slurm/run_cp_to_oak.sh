#!/bin/bash
#SBATCH --job-name=cp_fastq
#SBATCH --output=cp_fastq.out
#SBATCH --error=cp_fastq.err
#SBATCH --partition=biochem
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

cp -r usftp21.novogene.com/01.RawData/RDX112F_RTB000 /oak/stanford/groups/rhiju/sherlock/scratch/rhiju/Novogene/
echo "DONE"
