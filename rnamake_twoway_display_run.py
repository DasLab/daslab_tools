#!/usr/bin/env python3
import argparse
import os
import time
import shutil

parser = argparse.ArgumentParser(
                    prog = 'rnamake_twoway_display_run',
                    description = 'Wrapper around RNAmake design_rna_scaffold to display TWOWAY RNA motifs in mini-TTR nanostructures' )

parser.add_argument('-e','--extra_pdbs', required=True, nargs='+', help='PDB file with TWOWAY junction motif' )
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
assert( os.path.isdir(os.environ['RNAMAKE']) )
print('RNAMAKE dir =',os.environ['RNAMAKE'] )
assert( os.path.isfile( pdb ) )
assert( pdb[-4:] == '.pdb' )
for extra_pdb in args.extra_pdbs:
    assert( os.path.isfile( extra_pdb ) )
    assert( extra_pdb[-4:] == '.pdb' )


wd = args.outdir
if len(wd)>0:
    if wd[-1] != '/': wd += '/'
    if not os.path.isdir( wd ): os.makedirs( wd, exist_ok = True )


cwd = os.getcwd()


for extra_pdb in args.extra_pdbs:
    tag = os.path.basename(extra_pdb)[:-4]
    print( tag )

    # Do a run with TWOWAY junction PDB inserted into first leg of helix-2WJ-helix-2WJ-helix-2WJ-helix connector for tetraloop/receptor pdb "HXHJHJH"
    motif_tags = ['HXHJHJH','HJHXHJH','HJHJHXH']
    motif_paths = [ 'flex_helices,%s,flex_helices,new_twoways,flex_helices,new_twoways,flex_helices' % tag,
                    'flex_helices,new_twoways,flex_helices,%s,flex_helices,new_twoways,flex_helices' % tag,
                    'flex_helices,new_twoways,flex_helices,new_twoways,flex_helices,%s,flex_helices' % tag ]

    for (motif_tag,motif_path) in zip( motif_tags,motif_paths ):
        for cutoff in [15]: #[15,5]:
            wd_new = '%s%s/%s_cutoff_%d/' % (wd,tag,motif_tag,cutoff)

            if not os.path.isdir( wd_new ): os.makedirs( wd_new, exist_ok = True )
            pdb_name = os.path.basename(pdb)
            extra_pdb_name = os.path.basename(extra_pdb)
            if not os.path.isfile(wd_new + pdb_name ): shutil.copyfile(pdb, wd_new + pdb_name)
            if not os.path.isfile(wd_new + extra_pdb_name ): shutil.copyfile(extra_pdb, wd_new + extra_pdb_name )

            print('Going into',wd_new)
            os.chdir( wd_new )
            cmd = '%s --pdb %s --start_bp %s --end_bp %s --log_level debug --sequences_per_design 1 --designs %d --max_helix_length %d --search_type mc --motif_path %s  --search_cutoff %d --dump_pdbs --seq_opt_cutoff 15 --extra_pdbs %s > design.log 2> design.err' % (EXE, pdb_name, args.start_bp, args.end_bp, args.num_designs, cutoff, motif_path, cutoff, extra_pdb_name )
            print(cmd)
            os.system( cmd )
            os.chdir( cwd )

time_end=time.time()

print( '\nTotal time: ' + time.strftime("%H:%M:%S",time.gmtime(time_end-time_start) ) )

