#!/bin/bash
#SBATCH --job-name=cram2fastq
#SBATCH --output=cram2fastq.out
#SBATCH --error=cram2fastq.err
#SBATCH --partition=biochem
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

OAKDIR=/oak/stanford/groups/rhiju/sherlock/home/ultima_OpenKnot_20240712/CRAMS

samtools fastq $OAKDIR/404060-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-Openknot1-Lib-S-No-RTB007_Twist_OK1_SSIINomod.cram > 404060-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-RTB007_Twist_OK1_SSIINomod.fastq 2> 404060-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-RTB007_Twist_OK1_SSIINomod.err &
samtools fastq $OAKDIR/403767-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-Openknot1-Lib-S-No-RTB007_Twist_OK1_SSIINomod.cram > 403767-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-RTB007_Twist_OK1_SSIINomod.fastq 2> 403767-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-RTB007_Twist_OK1_SSIINomod.err &
samtools fastq $OAKDIR/404060-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-Openknot1-Lib-M-No-RTB001_Twist_OK1_MaraNomod.cram > 404060-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-RTB001_Twist_OK1_MaraNomod.fastq 2> 404060-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-RTB001_Twist_OK1_MaraNomod.err &
samtools fastq $OAKDIR/404060-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-Openknot1-Lib-2A3-RTB006_Twist_OK1_2A3.cram > 404060-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-RTB006_Twist_OK1_2A3.fastq 2> 404060-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-RTB006_Twist_OK1_2A3.err &
samtools fastq $OAKDIR/403767-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-Openknot1-Lib-2A3-RTB006_Twist_OK1_2A3.cram > 403767-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-RTB006_Twist_OK1_2A3.fastq 2> 403767-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-RTB006_Twist_OK1_2A3.err &
samtools fastq $OAKDIR/404060-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.cram > 404060-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-RTB000_Twist_OK1_DMS.fastq 2> 404060-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-RTB000_Twist_OK1_DMS.err &
samtools fastq $OAKDIR/403767-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-Openknot1-Lib-M-No-RTB001_Twist_OK1_MaraNomod.cram > 403767-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-RTB001_Twist_OK1_MaraNomod.fastq 2> 403767-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-RTB001_Twist_OK1_MaraNomod.err &
samtools fastq $OAKDIR/403767-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.cram > 403767-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.fastq 2> 403767-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.err &
wait

gzip 404060-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-RTB007_Twist_OK1_SSIINomod.fastq &
gzip 403767-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-RTB007_Twist_OK1_SSIINomod.fastq &
gzip 404060-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-RTB001_Twist_OK1_MaraNomod.fastq &
gzip 404060-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-RTB006_Twist_OK1_2A3.fastq &
gzip 403767-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-RTB006_Twist_OK1_2A3.fastq &
gzip 404060-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-RTB000_Twist_OK1_DMS.fastq &
gzip 403767-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-RTB001_Twist_OK1_MaraNomod.fastq &
gzip 403767-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.fastq &
wait

echo "DONE"