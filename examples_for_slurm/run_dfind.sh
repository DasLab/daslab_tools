#!/bin/bash
#SBATCH --job-name=dfind
#SBATCH --output=dfind.out
#SBATCH --error=dfind.err
#SBATCH --partition=biochem,owners
#SBATCH --time=8:00:00
#SBATCH -n 16
#SBATCH -N 1

ml reset
ml system mpifileutils
srun -n 16 dfind ./ -v -o dfind.log -t --size +1GB --atime +90

echo "DONE"
