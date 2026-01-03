#!/usr/bin/env python3
import argparse
import os
import shutil

parser = argparse.ArgumentParser(
                    prog = 'prepare_slurm.py',
                    description = 'Prepare SLURM submission scripts for Sherlock.',
                    epilog = 'Prepares run_slurm_*.sh for SLURM, and sbatch_commands.sh file to source. Assumes one core per job!')


parser.add_argument('commands_file',help='Text file with all commands in separate lines')
parser.add_argument('-j','--jobs_per_slurm_node', default=24,type=int,help='Number of jobs for each node' )
parser.add_argument('-m','--memory_per_job', default=2,type=int,help='Number of Gb memory per job. Assume one core per job!')
parser.add_argument('-n','--job_name', default='',help='Name of job for slurm')
parser.add_argument('-t','--job_time', default=48,type=int,help='Number of hours to request per node (default 48)')
parser.add_argument('-b','--bundle', default=1,type=int,help='Number of commands to bundle (default 1)')

args = parser.parse_args()
commands_file = args.commands_file
job_name = args.job_name
if len(job_name)==0: job_name = commands_file.replace('.sh','').replace('.txt','')

assert( os.path.isfile( commands_file ) )
command_lines = [x.strip()  for x in open( commands_file ).readlines() if len(x.strip())>0 and x.strip()[0] != '#' ]

# bundle command lines together
if args.bundle > 1:
    command_lines_bundle = []
    command = ''
    for (i,command_line) in enumerate(command_lines):
        if ( i % args.bundle == 0 ):
            if len(command)>0: command_lines_bundle.append( command )
            command = ''
        else:
            command += ' && '
        if command_line.endswith('&'): command_line = command_line[:-1]
        command += command_line
    print( f'Bundled {len(command_lines)} commands into {len(command_lines_bundle)}' )
    command_lines = command_lines_bundle

slurm_file_count = 1
slurm_file_dir = 'slurm_files'
os.makedirs(slurm_file_dir, exist_ok=True )
fid_slurm = open( '%s/run_slurm_%03d.sh' % (slurm_file_dir, slurm_file_count), 'w' )
fid_sbatch_commands = open( 'sbatch_commands.sh', 'w')
fid_bash_commands = open( 'bash_commands.sh', 'w')
num_command_lines = len( command_lines)

commands = []
for (i,command_line) in enumerate(command_lines):
    command = command_line
    if command[-1] != '&': command += ' &'
    commands.append( command )
    if (i+1) % args.jobs_per_slurm_node == 0 or (i+1) == num_command_lines:
        njobs = len(commands)
        sbatch_preface = '#!/bin/bash\n#SBATCH --job-name=%s\n#SBATCH --output=%s.o%%j\n#SBATCH --error=%s.e%%j\n#SBATCH --partition=biochem,owners\n#SBATCH --time=%d:00:00\n#SBATCH -n %d\n#SBATCH -N 1\n#SBATCH --mem=%dG\n\n' \
                 % (job_name,job_name,job_name,args.job_time,njobs,args.memory_per_job * njobs)
        fid_slurm.write( sbatch_preface )
        for command in commands: fid_slurm.write( command +'\n' )
        fid_slurm.write('\nwait\necho "DONE"\n')
        fid_slurm.close()
        fid_sbatch_commands.write('sbatch %s\n' % fid_slurm.name )
        fid_bash_commands.write('source %s\n' % fid_slurm.name )
        slurm_file_count += 1
        if (i+1) < num_command_lines:
            fid_slurm = open( '%s/run_slurm_%03d.sh' % (slurm_file_dir, slurm_file_count), 'w' )
            commands = []

print( "\nTo queue up %d slurm jobs with %d command lines on sherlock you can run:\n source %s\n" % (slurm_file_count-1,num_command_lines,fid_sbatch_commands.name) )

fid_sbatch_commands.close()
fid_bash_commands.close()

