#!/usr/bin/env python

from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='fungidb_tools',
      version='0.1',
      description='Tools for maintaining and developing FungiDB',
      long_description=readme(),
      url='http://github.com/edliaw/fungidb_tools',
      author='Edward Liaw',
      author_email='ed.liaw@fungidb.org',
      packages=['fungidb_tools'],
      scripts=[
          'scripts/datasets/generate_datasets',
          'scripts/datasets/generate_orgn_datasets',
          'scripts/datasets/sra_downloader',
          'scripts/isf/format_fasta',
          'scripts/isf/format_gff',
          'scripts/isf/format_mips',
          'scripts/isf/generate_chr_map',
          'scripts/isf/split_algids',
          'scripts/isf/undo_algids',
          'scripts/isf/extract_aliases',
      ],
      install_requires=[
          'biopython',
          'lxml',
          'gdata',
          'decorator',
      ],
      zip_safe=False,)
