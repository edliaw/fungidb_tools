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
  * simple_gdata: for wrapping the gdata library into an easier-to-use format.  Primarily to download and edit spreadsheets on Google Drive.
  * datasets: for turning the Genomes spreadsheet into XML workflow config files.
  * xml: additional tools for working with XML files.
  * naming: for naming organisms according to stricter specifications than is enforced by EuPathDB.
* NCBI
  * aspera: for downloading SRA datasets from NCBI.
  * simple_eutils: for wrapping NCBI eutils to interface with NCBI
