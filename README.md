fungidb_tools
=============

Scripts for maintenance, data loading, and validation for FungiDB.

Prerequisites
-------------

* python2.7 compiled with _curses, _ssh
* biopython, lxml, gdata, decorator

Installation
------------

```
python2.7 setup.py install
or
python2.7 setup.py develop
```

Modules
-------

* Datasets
  * simple_gdata: Wrapper around the gdata library to make it easier to use.  Used to interface with spreadsheets on Google Drive.
  * datasets: Turns the Genomes spreadsheet into XML workflow config files.
  * xml: Additional tools for working with XML files.
  * naming: Naming organisms with more consistent specifications than is enforced by EuPathDB.
* NCBI
  * aspera: For downloading SRA datasets from NCBI.
  * simple_eutils: Wrapper around NCBI eutils to combine/simplify functions.

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
