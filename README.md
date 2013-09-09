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
```

Modules
-------

* Datasets
  * simple_gdata: wrapping around the gdata library for an easier-to-use format.  Primarily to download and edit spreadsheets on Google Drive.
  * datasets: for turning the Genomes spreadsheet into XML workflow config files.
  * xml: additional tools for working with XML files.
  * naming: for naming organisms according to stricter specifications than is enforced by EuPathDB.
* NCBI
  * aspera: for downloading SRA datasets from NCBI.
  * simple_eutils: wrapping around NCBI eutils to combine/simplify functions.

Scripts
-------

* ISF (Insert Sequence Features)
  * Reformatters, data extraction for gtf, gff3, fasta, and genbank filetypes.
* Datasets
  * Interact with data from the FungiDB Genomes spreadsheet.

Makefiles
---------

* ISF
  * Process genomic files for loading.
* Workflow
  * Shortcuts to interact with the workflow and EuPath toolchain.
