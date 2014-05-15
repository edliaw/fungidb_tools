fungidb_tools
=============

Scripts for maintenance, data loading, and validation for FungiDB.

Prerequisites
-------------

* python3 compiled with _curses, _ssh
* biopython, lxml, gdata, decorator

Installation
------------

```
python3 setup.py install
or
python3 setup.py develop
```

Modules
-------

* Datasets
  * datasets: Turn the Genomes spreadsheet into XML workflow config files.
  * isf: Reformat and extract data from genome files.
  * naming: Naming organisms with more consistent specifications than is enforced by EuPathDB.
* NCBI
  * aspera: For downloading SRA datasets from NCBI.
  * simple_eutils: Wrapper around NCBI eutils to combine/simplify functions.
* Other
  * elementlib: Tools for working with XML files.
  * json_gspread: Convert old-style Google Spreadsheet into JSON structure.

Scripts
-------

* ISF (Insert Sequence Features)
  * Reformatters, data extraction for gtf, gff3, fasta, and genbank filetypes.
* Datasets
  * Interact with data pulled from the FungiDB Genomes spreadsheet.

Makefiles
---------

* ISF
  * Process genomic files for loading.
* Workflow
  * Shortcuts to interact with the workflow and EuPath toolchain.
