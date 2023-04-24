#!/bin/bash
#SBATCH --job-name=ubr_split
#SBATCH --output=ubr_split.out
#SBATCH --error=ubr_split.err
#SBATCH --partition=biochem,owners
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=12
#SBATCH --mem=24G
##SBATCH --mail-type=ALL

FASTQ_DIR=/scratch/groups/rhiju/rhiju/Novogene/usftp21.novogene.com/01.RawData/RDX112F_RTB000/

ubr_split.py -q 1000000 -s pseudoknot50_puzzle_11318423.tsv.RNA_sequences.fa  -b RTBbarcodes_PK50_RNA.fasta -1  $FASTQ_DIR/RDX112F_RTB000_CKDL230001441-1A_HT3F2DSX5_L4_1.fq.gz -2 $FASTQ_DIR/RDX112F_RTB000_CKDL230001441-1A_HT3F2DSX5_L4_2.fq.gz --output_raw_counts --no_length_cutoff 

echo "DONE"
