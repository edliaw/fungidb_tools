"""Download files from NCBI using aspera connect (faster than FTP).

2013/01/03
Edward Liaw

"""
from __future__ import unicode_literals
import subprocess
import os


aspera_dir = os.getenv('ASPERA_HOME', '~/.aspera/connect')


class Aspera(object):

    """Find Aspera runtime files on the path."""

    def __init__(self, base_dir=aspera_dir,
                 opts=('-k', '1', '-l', '300M', '-QTr')):
        base_dir = os.path.expanduser(base_dir)
        dsa = os.path.join(base_dir, "etc/asperaweb_id_dsa.putty")
        ascp = os.path.join(base_dir, "bin/ascp")

        assert os.path.exists(base_dir), \
            "Aspera path does not exist at %s" % base_dir
        assert os.path.isfile(dsa), \
            "Aspera dsa key missing at %s" % dsa
        assert os.path.isfile(ascp) and os.access(ascp, os.X_OK), \
            "Aspera plugin missing at %s" % ascp

        self._ascp = ascp
        self._opts = opts + ('-i', dsa)

    def fetch(self, target, out_dir=os.path.curdir):
        """Call Aspera and return the call result."""
        call_path = (self._ascp,) + self._opts + (target, out_dir)
        return subprocess.call(call_path)
