#! /usr/bin/env python3
import argparse
import subprocess
import sys

parser = argparse.ArgumentParser(
                    prog = 'cram_to_counts.py',
                    epilog = 'Extremely basic histogram of counts assigned to each sequence.'
    )

parser.add_argument('--cram', required=True,default='RTB010_CustomArray_PK50_1M7_BindTheFivePrimeEnd.cram.txt',help='CRAM-formatted file')
args = parser.parse_args()

cramfile  = args.cram
assert( cramfile.find('.cram')>-1 )
outfile = cramfile.replace('.cram','.counts.csv')

count = 0
counts = {}
process = subprocess.Popen( ['samtools','view',cramfile], stdout=subprocess.PIPE)
while process.stdout.readable():
    line = process.stdout.readline()
    if not line: break
    if len(line)>0 and line[0]=='@': continue
    count += 1
    cols = line.split()
    seq = cols[2]
    if not seq in counts.keys(): counts[seq] = 0
    counts[ cols[2] ] += 1

f = open(outfile, 'w')
f.write('seq_id,counts\n')
for seq in counts.keys():
    f.write('%s,%d\n' % (seq.decode(),counts[seq]) )
f.close()

print('Wrote %d lines into %s\n' % (count,outfile) )


