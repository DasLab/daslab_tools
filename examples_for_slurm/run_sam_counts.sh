#!/bin/bash
#SBATCH --job-name=samcounts
#SBATCH --output=samcounts.out
#SBATCH --error=samcounts.err
#SBATCH --partition=biochem
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

OAKDIR=/oak/stanford/groups/rhiju/sherlock/home/ultima/ultima_OpenKnotUnTrimmed_20240717/CRAMS

sam_counts.py --cram $OAKDIR/404060-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-Openknot1-Lib-S-No-RTB007_Twist_OK1_SSIINomod.cram &
sam_counts.py --cram $OAKDIR/403767-Openknot1-Lib-S-No-Z0115-CGGCTAGATGCAGAT-Openknot1-Lib-S-No-RTB007_Twist_OK1_SSIINomod.cram &
sam_counts.py --cram $OAKDIR/404060-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-Openknot1-Lib-M-No-RTB001_Twist_OK1_MaraNomod.cram &
sam_counts.py --cram $OAKDIR/404060-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-Openknot1-Lib-2A3-RTB006_Twist_OK1_2A3.cram &
sam_counts.py --cram $OAKDIR/403767-Openknot1-Lib-2A3-Z0114-CAACATACATCAGAT-Openknot1-Lib-2A3-RTB006_Twist_OK1_2A3.cram &
sam_counts.py --cram $OAKDIR/404060-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.cram &
sam_counts.py --cram $OAKDIR/403767-Openknot1-Lib-M-No-Z0113-CAGTTCATCTGTGAT-Openknot1-Lib-M-No-RTB001_Twist_OK1_MaraNomod.cram &
sam_counts.py --cram $OAKDIR/403767-Openknot1-Lib-DMS-Z0008-CACATCCTGCATGTGAT-Openknot1-Lib-DMS-RTB000_Twist_OK1_DMS.cram &
wait

echo "DONE"
