#!/usr/bin/env python3

import argparse
import os
import shutil
import time
import glob

parser = argparse.ArgumentParser(
                    prog = 'rnamake_twoway_display_setup.py',
                    description = 'Set up slurm scripts for twoway_display.py.',
                    epilog = 'Split PDB files and prepare independent job directories and command-lines.')

parser.add_argument('-e','--extra_pdbs', nargs='+', required=True)
parser.add_argument('--pdbs_per_job', default=4, type=int, help='number of separate TWOWAY junctions to put in each CPU' )
parser.add_argument('--jobs_per_slurm_node', default=16, type=int, help='number of CPUs to ask for per SLURM job' )
parser.add_argument('-p','--pdb', type=str, help='PDB file with tetraloop receptor', default='updated_ttr.pdb' )
parser.add_argument('--start_bp', type=str, help='start BP', default='A18-A27' )
parser.add_argument('--end_bp', type=str, help='end BP', default='A8-A9' )
parser.add_argument('--num_designs', type=int, help='Number of designs', default=1 )
parser.add_argument('-O','--outdir',default='OUTPUT/')

args = parser.parse_args()
pdb = args.pdb

time_start = time.time()

# Check executables and input files
assert( len(os.environ['RNAMAKE']) > 0 )
EXE = 'design_rna_scaffold'
assert( shutil.which( EXE ) )
assert( shutil.which('rnamake_twoway_display_run.py') )
assert( os.path.isdir(os.environ['RNAMAKE']) )
original_RNAMAKE = os.environ['RNAMAKE']
assert( os.path.isfile( pdb ) )
assert( pdb[-4:] == '.pdb' )
for extra_pdb in args.extra_pdbs:
    assert( os.path.isfile( extra_pdb ) )
    assert( extra_pdb[-4:] == '.pdb' )

# Create job directories and compile all commands
all_commands_file = 'all_commands.sh'
fid_all = open( all_commands_file, 'w' )

slurm_file_dir = 'slurm_files'
os.makedirs(slurm_file_dir, exist_ok=True )

slurm_file_count = 1
fid_slurm = open( '%s/run_slurm_%03d.sh' % (slurm_file_dir, slurm_file_count), 'w' )
sbatch_preface = '#!/bin/bash\n#SBATCH --job-name=rnamake_run\n#SBATCH --output=rnamake_run.o%%j\n#SBATCH --error=rnamake_run.e%%j\n#SBATCH --partition=biochem,owners\n#SBATCH --time=48:00:00\n#SBATCH -n %d\n#SBATCH -N 1\n#SBATCH --mem=%dG\n\nml load gcc/12.1.0\n' % (args.jobs_per_slurm_node,2*args.jobs_per_slurm_node)
fid_slurm.write( sbatch_preface )
fid_sbatch_commands = open( 'sbatch_commands.sh', 'w')

extra_pdbs_for_command_line = []
num_commands = 0
num_jobs = 0
tot_jobs = 0
for (i,extra_pdb) in enumerate(args.extra_pdbs):

    extra_pdbs_for_command_line.append( extra_pdb )
    if len( extra_pdbs_for_command_line ) == args.pdbs_per_job or i == len( args.extra_pdbs )-1:
        extra_pdbs_string = ' '.join(extra_pdbs_for_command_line)
        hashdir = hash(extra_pdbs_string)
        command = '\ncp -r %s /tmp/%d\n' % (original_RNAMAKE,hashdir)
        command += 'export RNAMAKE=/tmp/%d\n' % hashdir
        command += 'rnamake_twoway_display_run.py --extra_pdbs %s -p %s --start_bp %s --end_bp %s --num_designs %d -O %s &\n' %( extra_pdbs_string, args.pdb, args.start_bp, args.end_bp, args.num_designs, args.outdir )
        fid_all.write( command  )
        fid_slurm.write( command  )
        extra_pdbs_for_command_line = []
        num_jobs += 1
        tot_jobs += 1

    num_commands += 1
    if (num_jobs == args.jobs_per_slurm_node) or i == len(args.extra_pdbs)-1:
        fid_slurm.write('\nwait\necho "DONE"\n')
        fid_slurm.close()
        fid_sbatch_commands.write('sbatch %s\n' % fid_slurm.name )
        if i < len(args.extra_pdbs)-1:
            fid_slurm = open( '%s/run_slurm_%03d.sh' % (slurm_file_dir, slurm_file_count), 'w' )
            fid_slurm.write( sbatch_preface )
            slurm_file_count += 1
            num_jobs = 0

time_end = time.time()
print( '\nTotal time: ' + time.strftime("%H:%M:%S",time.gmtime(time_end-time_start) ) )

print( '\n\nAll %d extra_pdbs within %d jobs can be run with:\n source %s' % (num_commands,tot_jobs,fid_all.name) )

print( '\n\nAll %d extra_pdbs within %d jobs in %d SLURM scripts can be run with:\n source %s' % (num_commands,tot_jobs,slurm_file_count,fid_sbatch_commands.name) )


fid_all.close()
fid_sbatch_commands.close()

