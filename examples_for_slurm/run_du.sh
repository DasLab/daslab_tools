#!/bin/bash
#SBATCH --job-name=du
#SBATCH --output=du.o%j
#SBATCH --error=du.e%j
#SBATCH --partition=biochem
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

du -h -d 1
echo "DONE"
