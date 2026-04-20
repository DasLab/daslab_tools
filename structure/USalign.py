#!/usr/bin/env python3
"""
USalign.py

Wrapper script to run USalign on one or more PDB files against one or more
reference PDBs.

Behavior modes:
- Legacy (positional): If you do not provide -refpdb, use positional arguments:
    USalign.py ref.pdb query1.pdb query2.pdb ...
  The first positional file is treated as the single reference and the rest as
  queries (same as original behavior).

- New (flagged): Provide one or more reference PDBs with -refpdb and provide
  query PDBs with -pdb:
    USalign.py -refpdb "ref a.pdb" "ref b.pdb" -pdb "query*.pdb"
  If -refpdb is used, -pdb is required. Patterns (globs) are expanded. Filenames
  containing spaces are safely handled.

Other features:
- Uses subprocess (no shell string composition) so filenames with spaces are safe.
- Detects multimer references by counting TER lines in each reference PDB.
- Preserves most original CLI options and behavior.
- Verbose mode prints a shell-escaped command for inspection.
"""
from __future__ import annotations

import argparse
import glob
import re
import shlex
import subprocess
from os.path import exists
from sys import stderr, exit

def expand_patterns(patterns):
    """Expand a list of filename patterns (globs). Return sorted unique file list."""
    out = []
    for p in patterns:
        if exists(p):
            out.append(p)
        else:
            matches = sorted(glob.glob(p))
            if matches:
                out.extend(matches)
            else:
                # keep the literal so caller can detect missing files
                out.append(p)
    # remove duplicates while preserving order
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

def parse_usalign_output(lines):
    """Parse USalign stdout lines for TM-score, aligned length and RMSD."""
    TMscore = 0.0
    nalign = 0
    rmsd_align = 0.0
    for line in lines:
        # TM-score line: look for a numeric value on a TM-score line
        if 'Structure_2' in line and line.strip().lower().startswith('tm'):
            m = re.search(r'([0-9]*\.[0-9]+|\d+)', line)
            if m:
                try:
                    TMscore = float(m.group(1))
                except ValueError:
                    pass
        # Aligned length line: extract numbers (aligned length, RMSD)
        if line.strip().startswith('Aligned length'):
            cleaned = line.replace(',', '')
            nums = re.findall(r'\d+(?:\.\d+)?', cleaned)
            if len(nums) >= 1:
                try:
                    nalign = int(float(nums[0]))
                except ValueError:
                    pass
            if len(nums) >= 2:
                try:
                    rmsd_align = float(nums[1])
                except ValueError:
                    pass
    return TMscore, nalign, rmsd_align

def main():
    parser = argparse.ArgumentParser(description='Run USalign on a bunch of PDBs.')
    # New optional mode: multiple reference pdbs via -refpdb and queries via -pdb
    parser.add_argument('-refpdb', nargs='+',
                        help='Reference PDB file(s). If provided, -pdb must be used for queries.')
    parser.add_argument('-pdb', nargs='+',
                        help='PDB file(s) to align (use with -refpdb). Globs allowed.')

    # Legacy positional mode: first positional is ref, rest are queries
    parser.add_argument('inputs', nargs='*',
                        help='Legacy: first is ref PDB, rest are query PDBs (use when not using -refpdb).')

    parser.add_argument('-dump', action='store_true', help='Prepare superposition PDB as .TMsup.pdb ')
    parser.add_argument('-TMscore', type=int, default=0, help='integer setting for TMscore (0 by default means ignore sequence) ')
    parser.add_argument('-RNA', action='store_true', help='only align RNA chains')
    parser.add_argument('-force_mm', action='store_true', help='force align multimer (default auto-detect)')
    parser.add_argument('-force_monomer', action='store_true', help='force align monomer (default auto-detect)')
    parser.add_argument('-mm', default=-1, type=int, help='force specific -mm in USalign')
    parser.add_argument('-atom', default="C3'", help='atom representative, up to 4 characters (default: "C3\'") ')
    parser.add_argument('-t', '--tabular', action='store_true', help='output in csv format')
    parser.add_argument('--hetatm', action='store_true', help='Use heteroatom residues in alignment')
    parser.add_argument('-ter', type=int, default=0, help='USalign mode to handle TER in multichain mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='print out the command line and output')

    args = parser.parse_args()

    # Determine mode and lists of reference and query patterns
    if args.refpdb:
        # Flagged mode: -refpdb provided -> -pdb required
        if not args.pdb:
            stderr.write("When using -refpdb you must provide query PDBs via -pdb\n")
            exit(1)
        ref_patterns = args.refpdb
        query_patterns = args.pdb
    else:
        # Legacy positional mode
        if not args.inputs or len(args.inputs) < 2:
            stderr.write("Legacy usage requires at least two positional arguments: refpdb and one or more pdbs\n")
            parser.print_usage()
            exit(1)
        ref_patterns = [args.inputs[0]]
        query_patterns = args.inputs[1:]

    # Expand patterns (globs) for references and queries
    ref_files = expand_patterns(ref_patterns)
    query_files = expand_patterns(query_patterns)

    # Verify reference files exist
    verified_refs = []
    for rf in ref_files:
        if not exists(rf):
            stderr.write(f'Could not find reference PDB file: {rf}\n')
            exit(1)
        verified_refs.append(rf)

    if len(verified_refs) == 0:
        stderr.write('No reference PDB files found.\n')
        exit(1)

    # Expand and verify queries; if a pattern resulted in unmatched literal, check and skip gracefully
    final_queries = []
    for q in query_files:
        if not exists(q):
            stderr.write(f'Could not find PDB file: {q}\n')
            continue
        final_queries.append(q)

    if len(final_queries) == 0:
        stderr.write('No query PDB files found.\n')
        exit(1)

    # basic validation
    if args.mm > -1:
        assert (not args.force_mm and not args.force_monomer)

    EXEC = 'USalign'

    if args.tabular:
        print('%s,%s,%s' % ('ref', 'query', 'TMscore'))

    # For each reference, detect multimer (TER lines) and run USalign against each query
    for refpdb in verified_refs:
        # autodetect whether to use multimer by counting TER lines in the reference PDB
        try:
            with open(refpdb, 'r') as fh:
                ter_count = sum(1 for line in fh if line.strip().startswith('TER'))
        except Exception as e:
            stderr.write(f'Error reading reference PDB {refpdb}: {e}\n')
            continue

        # original behavior: use_mm = len(grep_results) > 1
        use_mm = ter_count > 1
        if args.force_mm:
            use_mm = True

        for pdb_path in final_queries:
            # Build argument list (avoid shell)
            cmd = [EXEC, pdb_path, refpdb, '-TMscore', str(args.TMscore), '-atom', args.atom]

            if args.RNA:
                cmd.extend(['-mol', 'RNA'])
            if use_mm and not args.force_monomer and not args.mm > -1:
                cmd.extend(['-mm', '1', '-ter', str(args.ter)])  # legacy
            if args.mm > -1:
                cmd.extend(['-mm', str(args.mm), '-ter', str(args.ter)])
            if args.hetatm:
                cmd.extend(['-het', '1'])
            if args.dump:
                sup_model_file = pdb_path.replace('.pdb', '') + '.TMsup.pdb'
                cmd.extend(['-o', sup_model_file])

            if args.verbose:
                if hasattr(shlex, 'join'):
                    print(shlex.join(cmd))
                else:
                    print(' '.join(shlex.quote(a) for a in cmd))

            # Run USalign
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except FileNotFoundError:
                stderr.write(f'Executable not found: {EXEC}\n')
                exit(1)
            except Exception as e:
                stderr.write(f'Error running {EXEC}: {e}\n')
                exit(1)

            stdout_lines = res.stdout.splitlines()
            if args.verbose and res.stderr:
                for l in res.stderr.splitlines():
                    print(l)

            if args.verbose:
                for line in stdout_lines:
                    print(line.strip())

            TMscore, nalign, rmsd_align = parse_usalign_output(stdout_lines)

            if args.tabular:
                print('%s,%s,%f' % (refpdb, pdb_path, TMscore))
            else:
                print('%s -vs- %s: %9.5f over %d residues   TM-score: %f' %
                      (refpdb, pdb_path, rmsd_align, nalign, TMscore))

if __name__ == '__main__':
    main()
