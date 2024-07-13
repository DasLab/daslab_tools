#!/bin/bash
#SBATCH --job-name=P240cp
#SBATCH --output=P240cp.out
#SBATCH --error=P240cp.err
#SBATCH --partition=biochem
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

time cp /oak/stanford/groups/rhiju/sherlock/home/ultima_LongRun_404888/Das_Long_240bp.cram .
echo "DONE"
