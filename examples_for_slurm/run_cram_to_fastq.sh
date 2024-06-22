#!/bin/bash
#SBATCH --job-name=cram2fastq
#SBATCH --output=cram2fastq.out
#SBATCH --error=cram2fastq.err
#SBATCH --partition=biochem
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

#samtools head -n 100 /oak/stanford/groups/rhiju/sherlock/home/ultima_LongRun_404888/Das_Long_240bp.cram | samtools fastq > Das_Long_240bp.fastq
samtools fastq /oak/stanford/groups/rhiju/sherlock/home/ultima_LongRun_404888/Das_Long_240bp.cram > Das_Long_240bp.fastq
gzip Das_Long_240bp.fastq

echo "DONE"
