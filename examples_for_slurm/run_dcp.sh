#!/bin/bash
#SBATCH --job-name=dcp
#SBATCH --output=dcp.o%j
#SBATCH --error=dcp.e%j
#SBATCH --partition=biochem,owners
#SBATCH --time=2:00:00
#SBATCH -n 24
#SBATCH -N 1
#SBATCH --mem=16G

src_dir=Lane3_RPT
target_dir=Lane3_cmuts

echo "Copying ${src_dir} to ${target_dir}..."

ml reset
ml system mpifileutils
srun -n 24 dcp -p ${src_dir} ${target_dir}
# reset modules.
source ~/.bash_profile

echo "DONE"
