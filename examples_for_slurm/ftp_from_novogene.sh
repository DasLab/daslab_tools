#!/bin/bash
#SBATCH --job-name=download_seq
#SBATCH --output=download_seq.out
#SBATCH --error=download_seq.err
#SBATCH --partition=biochem,owners
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
wget -r -c ftp://X202SC23010609-Z01-F001:9xwy1dje@usftp21.novogene.com:21/
echo "DONE"
