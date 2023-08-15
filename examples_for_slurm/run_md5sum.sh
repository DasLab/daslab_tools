#!/bin/bash
#SBATCH --job-name=md5_fastq
#SBATCH --output=md5_fastq.out
#SBATCH --error=md5_fastq.err
#SBATCH --partition=biochem
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

md5sum *gz
echo "DONE"
