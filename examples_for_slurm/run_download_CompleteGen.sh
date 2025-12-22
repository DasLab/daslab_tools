#!/bin/bash
#SBATCH --job-name=md5_fastq
#SBATCH --output=md5_fastq.out
#SBATCH --error=md5_fastq.err
#SBATCH --partition=biochem
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
##SBATCH --mail-type=ALL

wget -O All_Fastqs_P150005811.tar 'https://cg-stanford.s3.us-west-1.amazonaws.com/All_Fastqs_P150005811.tar?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIA4AKLVTUS3GADZCGZ%2F20250602%2Fus-west-1%2Fs3%2Faws4_request&X-Amz-Date=20250602T201833Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=fb30ba428167733ef57ecc0461750e460baf039cd05d773a21a30e20db0cffc6'

md5sum *tar  > md5sum_CHECK.log
cat md5sum.All_Fastqs_P150005811.tar.txt >> md5sum_CHECK.log

tar xvf All_Fastqs_P150005811.tar 
echo 
echo "Decompressed: All_Fastqs_P150005811.tar "

echo "DONE"
