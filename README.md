# daslab_tools
Tools, mainly for cluster usage, for Das lab at Stanford

The `rna_tools` was developed initially in Rosetta, but is now maintained here.

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

## Directory structure

| Directory | Contents |
|-----------|----------|
| `structure/` | Structure analysis: USalign, lDDT, DSSR, OpenStructure, CIF parsing |
| `cluster/` | HPC job submission, rsync to/from cluster, Oak archival |
| `seq/` | Sequence tools: reverse complement, RNA→DNA, FASTQ/SAM utilities |
| `data/` | Data format conversion (CSV ↔ Parquet) |
| `rna_tools/` | RNA-specific tools, originally from Rosetta |
| `rna_tools/pdb_util/` | PDB structure utilities |
| `rna_tools/silent_util/` | Rosetta silent file utilities |
| `rna_tools/cluster_setup/` | Cluster job setup |
| `rna_tools/job_setup/` | Job configuration |
| `rna_tools/cif_util/` | CIF file utilities |

## TODO
- Update all tools to use `argparse` (which was not available when many of these tools were written) to more robustly handle arguments.
- Use an LLM to document all scripts.
- Provide some examples.
- Make all the pdb_tools compatible with modern CIF format and gzip.
- Fill out documentation in this README.

