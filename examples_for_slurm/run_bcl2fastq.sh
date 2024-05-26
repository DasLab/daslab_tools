#!/bin/bash
#SBATCH --job-name=bcl2fq
#SBATCH --output=bcl2fq.out
#SBATCH --error=bcl2fq.err
#SBATCH --partition=biochem,owners
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=15G
##SBATCH --mail-type=ALL

module load biology bcl2fastq
bcl2fastq --no-lane-splitting --minimum-trimmed-read-length 20 --mask-short-adapter-reads 10

echo "DONE"
