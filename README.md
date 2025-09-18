# daslab_tools
Tools, mainly for cluster usage, for Das lab at Stanford

The `rna_tools` was developed initially in Rosetta, but is now maintained here.

## Getting started

For the python tools, add to your `~/.bashrc`:

```
source ~/src/daslab_tools/rna_tools/INSTALL 
export PATH=$PATH:$HOME/src/daslab_tools
export PYTHONPATH=$PYTHONPATH:$HOME/src/daslab_tools
```

and `source ~/.bashrc`.

## TODO
- Update all tools to use `argparse` (which was not available when many of these tools were written) to more robustly handle arguments. 
- Use an LLM to document all scripts.
- Provide some examples. 
- Reorganize into directories that make sense, esp. the new CIF tools. 
- Make all the pdb_tools compatible with modern CIF format and gzip. 
- Fix the `INSTALL` script to go into subdirectories of the main directory; replace with something more concise. 
- Fill out documentation in this README.  

