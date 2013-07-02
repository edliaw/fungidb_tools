#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""Download files using aspera connect.

2013/01/03
Edward Liaw
"""
from __future__ import print_function
import subprocess
import os


class Aspera(object):
    def __init__(self, base_dir="~/.aspera/connect",
                 opts=('-k', '1', '-l', '300M', '-QTr')):
        base_dir = os.path.expanduser(base_dir)
        dsa = os.path.join(base_dir, "etc/asperaweb_id_dsa.putty")
        ascp = os.path.join(base_dir, "bin/ascp")

        assert os.path.exists(base_dir), "Aspera path does not exist at %s" % base_dir
        assert os.path.exists(dsa), "Aspera dsa key missing at %s" % dsa
        assert os.path.exists(ascp), "Aspera plugin missing at %s" % ascp

        self._ascp = ascp
        self._opts = opts + ('-i', dsa)

    def fetch(self, target, out_dir=os.path.curdir):
        call_path = (self._ascp,) + self._opts + (target, out_dir)
        return subprocess.call(call_path)
