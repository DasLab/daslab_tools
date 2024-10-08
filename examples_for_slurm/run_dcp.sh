#!/bin/bash
#SBATCH --job-name=dcp
#SBATCH --output=dcp.o%j
#SBATCH --error=dcp.e%j
#SBATCH --partition=biochem,owners
#SBATCH --time=2:00:00
#SBATCH -n 16
#SBATCH -N 1
#SBATCH --mem=16G

#src_dir=/scratch/groups/rhiju/rhiju/Experiments/Eterna_RYOP_Pilot2022_experiments/DataAnalysis/Data/NovaSeq_2023-08-02_RH_VW_MutMap
#target_dir=/scratch/users/rhiju/Experiments/Eterna_RYOP_Pilot2022_experiments/DataAnalysis/Data/NovaSeq_2023-08-02_RH_VW_MutMap

#src_dir=/scratch/groups/rhiju/rhiju/Experiments/Eterna_RYOP_Pilot2022_experiments/DataAnalysis/Data/NovaSeq_2023-08-01_RH_DasBigLib0-15k
#target_dir=NovaSeq_2023-08-01_RH_DasBigLib0-15k

#src_dir=/scratch/groups/rhiju/rhiju/Experiments/Eterna_RYOP_Pilot2022_experiments/DataAnalysis/Data/NovaSeq_2023-07-28_RH_OpenKnot1
#target_dir=NovaSeq_2023-07-28_RH_OpenKnot1

src_dir=/scratch/groups/rhiju/rhiju/Experiments/Eterna_RYOP_Pilot2022_experiments/DataAnalysis/Data/NovaSeq_2023-06-06_RH_SL5_M2seq
target_dir=NovaSeq_2023-06-06_RH_SL5_M2seq

echo "Copying ${src_dir} to ${target_dir}..."

ml reset
ml system mpifileutils
srun -n 16 dcp -p ${src_dir} ${target_dir}
# reset modules.
source ~/.bash_profile

echo "DONE"
