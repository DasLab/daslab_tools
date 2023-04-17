#!/bin/bash
#SBATCH --job-name=ubr_merge
#SBATCH --output=ubr_merge.out
#SBATCH --error=ubr_merge.err
#SBATCH --partition=biochem,owners
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
##SBATCH --mail-type=ALL

ubr_merge.py UBR  > ubr_merge.out 2> ubr_merge.err 

echo "DONE"
