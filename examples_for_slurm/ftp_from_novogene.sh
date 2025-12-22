#!/bin/bash
#SBATCH --job-name=download_seq
#SBATCH --output=download_seq.out
#SBATCH --error=download_seq.err
#SBATCH --partition=biochem,owners
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

# Figure this out, and very ftp access, from a quick pilot run with "bash ftp_from_novogene.sh"
DIRNAME=MOHCA_pilot2

# This is new command for ftp -- copy/paste from Novogene e-mail 
lftp -c 'set sftp:auto-confirm yes;set net:max-retries 20;open sftp://X202SC25037762-Z01-F004:yeyd5j9s@usftp23.novogene.com; mirror --verbose --use-pget-n=8 -c'

mv 01.RawData/${DIRNAME} .
md5sum ${DIRNAME}/*gz
cat ${DIRNAME}/MD5.txt

echo "If MD5 matches, type:"
echo " rm -rf usftp21.novogene.com"
echo "DONE"
