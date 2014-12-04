#!/usr/bin/env python
"""fungidb-tools setup file."""
from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='fungidb_tools',
      version='0.1',
      description='Tools for maintaining and developing FungiDB',
      author='Edward Liaw',
      author_email='ed.liaw@fungidb.org',
      long_description=readme(),
      url='http://github.com/edliaw/fungidb_tools',

      packages=find_packages(),

      scripts=[
          'scripts/datasets/generate_datasets',
          'scripts/datasets/pull_spreadsheet',
          'scripts/datasets/download_sra',
          'scripts/datasets/download_genbank',
          'scripts/isf/format_fasta',
          'scripts/isf/format_gff',
          'scripts/isf/format_mips',
          'scripts/isf/gen_fasta_chr_map',
          'scripts/isf/gen_genbank_chr_map',
          'scripts/isf/split_algids',
          'scripts/isf/undo_algids',
          'scripts/isf/extract_gff3_attr',
          'scripts/isf/extract_products_broad',
          'scripts/isf/extract_products_genbank',
          'scripts/isf/extract_products_jgi',
      ],

      test_suite="fungidb_tools.tests",

      install_requires=[
          'future',
          'biopython',
          'lxml',
          'gspread',
          'decorator',
      ],)
