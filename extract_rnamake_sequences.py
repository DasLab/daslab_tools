#!/usr/bin/env python3

import argparse
import os
import shutil
import time
import glob
import random

parser = argparse.ArgumentParser(
                    prog = 'extract_rnamake_sequences.py',
                    description = 'Go through output of RNAMake runs from rnamake_twoway_display_run.py',
                    epilog = 'Handles a lot of mangling in RNAMake''s current output.')

parser.add_argument('-O','--outdir',default='OUTPUT')
parser.add_argument('-ml','--max_length',default=100,type=int);

args = parser.parse_args()
MAX_LENGTH = args.max_length

time_start = time.time()
grepfile = 'ALL.scores'

if not os.path.exists( grepfile ):
    command = 'find %s -name default.scores | xargs grep FLEX > %s' % (args.outdir,grepfile)
    print(command)
    os.system(command)

lines = open( grepfile ).readlines()
solutions = []
runs = []
solutions_by_run = {}
for line in lines:
    cols = line.split(',')
    if len(cols)<4: continue
    firstcols = cols[0].split(':')
    if len(firstcols) < 2: continue
    if not firstcols[1].isnumeric(): continue
    count_in_file = int(firstcols[1])
    run = firstcols[0]
    run = run.replace('/default.scores','')
    run = run.replace('OUTPUT//','')
    run = run.replace('OUTPUT/','')
    if run not in runs:
        runs.append(run)
        solutions_by_run[run] = []
    solstring = cols[2] # sequence with N's in helices
    sequence  = cols[-4]
    pdbname = 'design.%d.pdb' % count_in_file

    if len(sequence) == 0: continue
    if len(sequence) > MAX_LENGTH: continue
    if len(sequence)!=len(solstring): continue
    solution = (sequence,solstring,pdbname)
    solutions.append( solution )
    solutions_by_run[run].append( solution )

# Choose min length solution
data_output = []
for run in runs:
    solutions_for_run = solutions_by_run[run]
    if len(solutions_for_run) == 0: continue
    best_solution = solutions_for_run[0]
    for solution in solutions_for_run:
        if len( solution[0] )  < len( best_solution[0] ):
            best_solution = solution
    title = '%s/%s' % (run,best_solution[2])
    data_output.append( (title,best_solution[0],best_solution[1] ) )

# Design perturbing mutations -- truncate longest and most central flex_helix; or insert up to 5 bp.
data_output_delhelix = []
data_output_inshelix = []
for out in data_output:
    title     = out[0]
    sequence  = out[1]
    solstring = out[2]
    Npos = []
    for (i,char) in enumerate(solstring):
        if char == 'N': Npos.append(i)
    # even number! Each NNN is balanced by a later NNN to define helix
    assert( len(Npos) % 2 == 0 )
    Nbp = int(len(Npos)/2)
    bp = {}
    for i in range(Nbp): bp[Npos[i]] = Npos[-1-i]
    # separate into helix stacks
    helix_len = 0
    helix_start = Npos[0]
    helices = []
    for (i,idx) in enumerate(Npos[:Nbp]):
        helix_len += 1
        if (i == len(Npos)-1) or Npos[i+1] != Npos[i]+1:
            helices.append( (helix_len,helix_start) )
            helix_len = 0
            if (i < len(Npos)-1): helix_start = Npos[i+1]
    # Find longest helix, break degeneracy by latest in sequence
    helices.sort(reverse=True) # get longest helix
    helix_len = helices[0][0]
    helix_start = helices[0][1]

    # Delete: longest flex_helix.
    delete_pos = []
    for i in range(helix_len):
        delete_pos.append( helix_start+i )
        delete_pos.append( bp[helix_start+i] )
    # prepare new sequence and title
    sequence_new = ''
    solstring_new = ''
    for i in range(len(sequence)):
        if i not in delete_pos:
            sequence_new += sequence[i]
            solstring_new += solstring[i]
    title_new = '%s:delete_%dbp_%d-%d_%d-%d' % (title,helix_len,
                                                helix_start+1,helix_start+helix_len,
                                                bp[helix_start]-helix_len+2,bp[helix_start]+1)
    data_output_delhelix.append((title_new,sequence_new,solstring_new))

    # Insert: Add up to 5 base pairs to longest flex helix
    n_extra_bps = int((MAX_LENGTH - len(sequence))/2)
    if (n_extra_bps == 0): continue
    nts = 'ACGU'
    rc = {'A':'U','U':'A','C':'G','G':'C'}
    extra_helix = ''
    extra_helix_rc = ''
    for i in range( n_extra_bps ): extra_helix += random.choice(nts)
    for i in range( n_extra_bps ): extra_helix_rc += rc[extra_helix[-1-i]]
    sequence_new  = sequence[:helix_start]  + extra_helix     + sequence[  helix_start:bp[helix_start]+1] + extra_helix_rc + sequence[ bp[helix_start]+1:]
    solstring_new = solstring[:helix_start] + 'X'*n_extra_bps + solstring[ helix_start:bp[helix_start]+1] + 'X'*n_extra_bps  + solstring[bp[helix_start]+1:]

    title_new = '%s:insert_%dbp_%d_%s_%d_%s' % (title,n_extra_bps,
                                              helix_start,extra_helix,
                                              bp[helix_start]+1,extra_helix_rc)

    assert(len(sequence_new) <= MAX_LENGTH)
    data_output_inshelix.append((title_new,sequence_new,solstring_new))

    #print( sequence)
    #print( solstring )
    #print( title_new )
    #print( sequence_new )
    #print( solstring_new )

def output_fasta(filename,data_output):
    fid = open(filename,'w')
    for out in data_output:
        fid.write('>%s\n%s\n\n' % (out[0],out[1]) )
    fid.close()
    print( '\nOutputted %d solutions to %s\n' % (len(data_output), fid.name) )

time_end = time.time()
print( '\nTotal time: ' + time.strftime("%H:%M:%S",time.gmtime(time_end-time_start) ) )
print( '\nFound %d min-length solutions, out of total %d runs containing %d solutions with length < %d out of %d total lines\n' % (len(data_output),len(runs),len(solutions),MAX_LENGTH,len(lines)) )

output_fasta( 'rnamake_minlength_solutions.fasta', data_output)
output_fasta( 'rnamake_minlength_solutions_DELETE_HELIX.fasta', data_output_delhelix )
output_fasta( 'rnamake_minlength_solutions_INSERT_HELIX.fasta', data_output_inshelix )


