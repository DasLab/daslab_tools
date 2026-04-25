# daslab_tools
Tools for the Das Lab at Stanford — cluster file transfer, structure analysis, sequence utilities, and RNA-specific PDB/silent-file processing.

The `rna_tools` directory was developed initially in Rosetta and is now maintained here. All scripts require Python 3 and accept `--help`.

## Getting started

Clone the repo to `~/src/daslab_tools`, then add the following to your `~/.bashrc`:

```bash
# daslab_tools — add root and all subdirectories to PATH and PYTHONPATH
export PATH="$PATH$(printf ':%s' $HOME/src/daslab_tools $HOME/src/daslab_tools/*/)"
export PYTHONPATH="$PYTHONPATH$(printf ':%s' $HOME/src/daslab_tools $HOME/src/daslab_tools/*/)"

# rna_tools subdirectories
export PATH="$PATH$(printf ':%s' $HOME/src/daslab_tools/rna_tools $HOME/src/daslab_tools/rna_tools/*/)"
export PYTHONPATH="$PYTHONPATH$(printf ':%s' $HOME/src/daslab_tools/rna_tools $HOME/src/daslab_tools/rna_tools/*/)"
```

Then run `source ~/.bashrc`. The glob `*/` picks up all subdirectories automatically, so no changes are needed when new subdirectories are added.

## Tools by directory

### `structure/`
- **`dssr.py`** — run x3dna-dssr on PDB files; prints dot-bracket secondary structure and sequence
- **`lddt.py`** — compute lDDT/ilDDT scores between a reference and one or more model structures (via OST)
- **`ost.py`** — run OST `compare-structures` on a reference vs. multiple PDBs
- **`split_models.py`** — split a multi-model PDB into individual numbered files
- **`thread_rna.py`** — thread a target sequence onto backbone atoms of a template PDB
- **`fix_o2prime.py`** — strip and rebuild O2′ atoms (fixes bad geometry from some structure predictors)
- **`USalign.py`** — wrapper for USalign structure superposition and TM-score

### `cluster/`
- **`rsync_to_cluster.py`** (`r2c`) — rsync files from the current directory to a named cluster destination
- **`rsync_from_cluster.py`** (`rfc`) — rsync files from a named cluster destination to the current directory
- **`cd_to_cluster.py`** (`c2c`) — print the equivalent of the current directory on another filesystem
- **`cluster_info.py`** — list known destinations; `cluster_info.py -a` shows resolved host and path for each
- **`prepare_slurm.py`** — generate SLURM sbatch scripts from a plain-text list of commands
- **`archive_to_oak.py`** — tar a directory and copy it to Oak long-term storage
- **`rosetta_submit.py`** — submit Rosetta jobs across cluster destinations

### `seq/`
- **`rc.py`** — reverse complement a DNA or RNA sequence
- **`rna2dna.py`** — convert an RNA sequence to DNA (U→T)
- **`gel_from_fastq.py`** — simulate a gel image from FASTQ read-length distribution
- **`sam_counts.py`** — count reads per reference sequence from a SAM file

### `data/`
- **`csv_to_parquet.py`** — convert a CSV file to Parquet
- **`parquet_to_csv.py`** — convert a Parquet file to CSV
- **`clean_parquet.py`** — filter or clean columns in a Parquet file

### `rna_tools/pdb_util/`
- **`renumber_pdb_in_place.py`** (`rpip`) — renumber residues in place; supports negative numbers and chain specs
- **`pdbsubset.py`** — extract specified residues from a PDB (by residue number, chain, or range)
- **`pdbslice.py`** — extract a contiguous range or custom subset/excision of residues
- **`extract_chain.py`** — extract one or more chains from a PDB (supports gzip)
- **`replace_chain.py`** / **`replace_chain_inplace.py`** — rename chain IDs in a PDB
- **`reorder_pdb.py`** / **`reorder_to_standard_pdb.py`** — reorder ATOM records to Rosetta or standard PDB order
- **`pdb2fasta.py`** — extract a FASTA-format sequence from a PDB
- **`get_sequence.py`** — print the residue sequence from a PDB
- **`get_res_num.py`** — list residue numbers present in a PDB
- **`check_cutpoints.py`** — identify chain cutpoints in a PDB
- **`make_rna_rosetta_ready.py`** — prepare an RNA PDB for Rosetta (renumber, strip ions, fix chains)
- **`fetch_pdb.py`** — download a PDB entry by accession code
- **`get_surrounding_res.py`** — find residues within a distance cutoff of a target residue
- **`rna_helix.py`** — build an ideal A-form RNA helix for a given sequence
- **`rna_mutate.py`** — mutate residues in an RNA PDB
- **`rna_thread.py`** — thread a new sequence onto an RNA backbone
- **`plot_contour.py`** — plot contour maps from `nucleobase_sample_around` score tables
- **`prepare_rna_puzzle_submissions.py`** — assemble a ranked multi-model PDB for RNA Puzzles submission

### `rna_tools/silent_util/`
- **`extract_lowscore_decoys.py`** (`ex`) — extract the lowest-scoring structures from a Rosetta silent file
- **`extract_lowscore_decoys_outfile.py`** (`exo`) — same, writing to a named output file
- **`extract_lowscore_decoys_multiple_outfiles.py`** — extract from multiple silent files in one call
- **`cat_outfiles.py`** — concatenate Rosetta silent/out files, deduplicating SEQUENCE and description headers
- **`fields.py`** (`fp`) — show which column numbers correspond to which score terms
- **`plot_score_vs_rms.py`** — scatter plot of score vs. RMS from one or more Rosetta .out files
- **`silent_file_sort_and_select.py`** — sort and filter a Rosetta silent file by score

### `rna_tools/job_setup/`
- **`rna_denovo_setup.py`** — generate Rosetta `rna_denovo` job scripts from sequence and secondary structure
- **`helix_preassemble_setup.py`** — set up helix pre-assembly jobs for Rosetta
- **`parallel_min_setup.py`** — set up parallel minimization jobs
- **`parse_tag.py`** / **`make_tag.py`** — parse and create Rosetta-style residue/chain tag strings
- **`rosetta_exe.py`** — locate Rosetta executables on the current system

### `rna_tools/cif_util/`
- **`extract_chain_from_cif.py`** — extract a single chain from an mmCIF file

## TODO
- Provide some examples.
- Make all the pdb_tools compatible with modern CIF format and gzip.

