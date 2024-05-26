#!/bin/bash
#SBATCH --job-name=untar_FILENAME
#SBATCH --output=untar_FILENAME.out
#SBATCH --error=untar_FILENAME.err
#SBATCH --partition=biochem,owners
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

tar xvfz /oak/stanford/groups/rhiju/sherlock/scratch/rhiju/Projects/RNAMake_revisit2023/twoway_display3.tgz
echo 
echo "Decompressed: /oak/stanford/groups/rhiju/sherlock/scratch/rhiju/Projects/RNAMake_revisit2023/twoway_display3.tgz"
echo "DONE"
