#!/bin/bash
#SBATCH --job-name=bcl2fq
#SBATCH --output=bcl2fq.out
#SBATCH --error=bcl2fq.err
#SBATCH --partition=biochem,owners
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=24
#SBATCH --mem=15G
##SBATCH --mail-type=ALL

module load biology bcl2fastq

bcl2fastq --minimum-trimmed-read-length 20 --mask-short-adapter-reads 10 --ignore-missing-bcls --loading-threads 4  --processing-threads 16 --writing-threads 4

#Original command line for Miseq runs. Seems to fail on bigger runs from, e.g., Novogene NovaSeq
#bcl2fastq --no-lane-splitting --minimum-trimmed-read-length 20 --mask-short-adapter-reads 10

echo "DONE"
