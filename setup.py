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
      install_requires=[
          'gdata',
          'lxml',
      ],
      zip_safe=False,)
