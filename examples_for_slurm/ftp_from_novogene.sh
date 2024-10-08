#!/bin/bash
#SBATCH --job-name=download_seq
#SBATCH --output=download_seq.out
#SBATCH --error=download_seq.err
#SBATCH --partition=biochem,owners
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

DIRNAME=PK50_ModU_Salt
#wget -r -c ftp://X202SC24086678-Z01-F003:fdkarp94@usftp21.novogene.com:21/
mv usftp21.novogene.com/01.RawData/${DIRNAME} .
md5sum ${DIRNAME}/*gz
cat ${DIRNAME}/MD5.txt
echo "If MD5 matches, type:"
echo " rm -rf usftp21.novogene.com"
echo "DONE"
