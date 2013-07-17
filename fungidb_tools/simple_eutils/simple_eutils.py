# -*- coding: utf-8 -*-
"""Simplify Bio.Entrez, with ElementTree parsing for efetch and esummary.

Esearch, elink, efetch, and esummary accept either an id argument or a webenv/
query_key pair to access a session history's results.  The advantage of using
the user session history is that it handles large queries better by avoiding
long query urls and allowing NCBI to pre-fetch information.

Two use-cases for esearch and elink:
    1. Get a list of ids.
    2. Get a session history that gives ids to the next query via a
       webenv/query_key pair.

Efetch and esummary results are parsed into an ElementTree for easier indexing.


Example use for quickly chaining together queries:

    from fungidb_tools import simple_eutils as eutils

    @eutils.retry  #fails only after a number of retries.
    def summary_from_search(db, term, field, out=None):
        webenv, query_key = eutils.webenv_search(db, term, field)
        return eutils.etree_summary(db, webenv=webenv, query_key=query_key, out=out)


2012/10/31
Edward Liaw
"""
from __future__ import print_function
import sys
import time
from decorator import decorator
from Bio import Entrez
from collections import Iterable
from types import StringTypes

try:
    from lxml import etree
except ImportError:
    try:
        import xml.etree.cElementTree as etree
        print("Running with cElementTree on Py2.5+", file=sys.stderr)
    except ImportError:
        import xml.etree.ElementTree as etree
        print("Running with ElementTree on Py2.5+", file=sys.stderr)


Entrez.email = "ed.liaw@fungidb.org"


class RetryException(Exception):
    pass


def _retry(func, *args, **kwargs):
    """Decorator: Allow retries in the event of a dropped query."""
    my_delay = func.delay  # nonlocal
    for x in range(func.attempts - 1):
        try:
            return func(*args, **kwargs)
        except AssertionError as e:
            # Allow debug error messages to raise.
            raise e
        except Exception as e:
            # Handle errors.
            print("Failed:", e, args, "Retry in %d.." % my_delay,
                  sep='\n', file=sys.stderr)
            time.sleep(my_delay)
            my_delay *= func.backoff  # Exponentially increase the delay.
    try:
        return func(*args, **kwargs)
    except:
        # Final error message.
        raise RetryException("%d retries failed." % func.attempts)


def retry(f, attempts=3, delay=3, backoff=2):
    """Decorator: Allow retries in the event of a dropped query."""
    f.attempts = attempts
    f.delay = delay
    f.backoff= backoff
    return decorator(_retry, f)


@retry
def webenv_post(db, id):
    """Get the webenv key from an epost (handles large lists of ids that may
    fail in hard-linked urls).

    Args:
        db: database to query
        id: string or list of ids

    Returns:
        Webenv and query key to access the session history.
    """
    if type(id) == list:
        # Accepts a list or comma-separated string.
        id = ','.join(id)

    post_handle = Entrez.epost(db=db, id=id)
    et = etree.parse(post_handle)
    post_handle.close()

    root = et.getroot()
    webenv = root.find('WebEnv').text
    query_key = root.find('QueryKey').text
    return webenv, query_key


@retry
def webenv_search(db, term=None, field=None, webenv=None, query_key=None):
    """Get the webenv key from an esearch.

    Args:
        db: database to query
        -- and --
        id: string or list of ids
        -- or --
        webenv: session history keys
        query_key

    Returns:
        Webenv and query key to access the session history.
    """
    search_handle = Entrez.esearch(db=db, term=term, field=field, retmax=0,
                                   webenv=webenv, query_key=query_key,
                                   usehistory='y')
    et = etree.parse(search_handle)
    search_handle.close()

    root = et.getroot()
    webenv = root.find('WebEnv').text
    query_key = root.find('QueryKey').text
    count = int(root.find('Count').text)
    return webenv, query_key, count


@retry
def webenv_link(db, dbfrom, id=None, webenv=None, query_key=None,
                linkname=None):
    """Get the webenv key from an elink map between two databases.

    Args:
        db: database to query
        dbfrom: ids must be from this database
        linkname (optional): specify a type of id to return (see:
            http://eutils.ncbi.nlm.nih.gov/entrez/query/static/entrezlinks.html)
        -- and --
        id: string or list of ids
        -- or --
        webenv: session history keys
        query_key

    Returns:
        Webenv and query key to access the session history.
    """
    if (not webenv and id) and (isinstance(id, Iterable) and
                                not isinstance(id, StringTypes)):
        webenv, query_key = webenv_post(dbfrom, id)
        id = None

    link_handle = Entrez.elink(db=db, dbfrom=dbfrom, id=id, linkname=linkname,
                               webenv=webenv, query_key=query_key,
                               cmd='neighbor_history')
    et = etree.parse(link_handle)
    link_handle.close()

    root = et.getroot()
    webenv = root.find('LinkSet/WebEnv').text
    query_key = root.find('LinkSet/LinkSetDbHistory/QueryKey').text
    return webenv, query_key


@retry
def idlist_search(db, term=None, field=None, webenv=None, query_key=None,
                  retmax=1000):
    """Find a list of ids from an esearch.

    Args:
        db: database to query
        -- and --
        id: string or list of ids
        -- or --
        webenv: session history keys
        query_key

    Returns:
        List of ids.
    """
    ids = []
    start = 0
    count = None
    while count is None or count > start:
        search_handle = Entrez.esearch(db=db, term=term, field=field,
                                       retstart=start, retmax=retmax,
                                       webenv=webenv, query_key=query_key,
                                       usehistory='y')
        et = etree.parse(search_handle)
        search_handle.close()

        root = et.getroot()
        count = int(root.find('Count').text)
        webenv = root.find('WebEnv').text
        query_key = root.find('QueryKey').text
        ids += [id.text for id in root.findall('IdList/Id')]
        start += retmax
    return ids


@retry
def idlist_link(db, dbfrom, id=None, webenv=None, query_key=None, linkname=None):
    """Find a list of ids from an elink map between two databases.

    Args:
        db: database to query
        dbfrom: ids must be from this database
        linkname (optional): specify a type of id to return (see:
            http://eutils.ncbi.nlm.nih.gov/entrez/query/static/entrezlinks.html)
        -- and --
        id: string or list of ids
        -- or --
        webenv: session history keys
        query_key

    Returns:
        List of ids.
    """
    if (not webenv and id) and (isinstance(id, Iterable) and
                                not isinstance(id, StringTypes)):
        webenv, query_key = webenv_post(dbfrom, id)
        id = None

    link_handle = Entrez.elink(db=db, dbfrom=dbfrom, id=id, linkname=linkname,
                               webenv=webenv, query_key=query_key)
    et = etree.parse(link_handle)
    link_handle.close()

    root = et.getroot()
    return [_id.text for _id in root.findall('LinkSet/LinkSetDb/Link/Id')]


def etree_summary(db, id=None, webenv=None, query_key=None, out=None):
    """Esummary wrapper.

    Args:
        db: database to query
        -- and --
        id: list/string of ids
        -- or --
        webenv: session history keys
        query_key

    Returns:
        ElementTree of results.
    """
    if (not webenv and id) and (isinstance(id, Iterable) and
                                not isinstance(id, StringTypes)):
        webenv, query_key = webenv_post(db, id)
        id = None

    summary_handle = Entrez.esummary(db=db, id=id,
                                     webenv=webenv, query_key=query_key)
    et = etree.parse(summary_handle)
    summary_handle.close()

    if out is not None:
        et.write(out)
    root = et.getroot()
    return root


def etree_fetch(db, id=None, webenv=None, query_key=None, out=None):
    """Efetch wrapper.

    Args:
        db: database to query
        -- and --
        id: list/string of ids
        -- or --
        webenv: session history keys
        query_key

    Returns:
        ElementTree of results.
    """
    if (not webenv and id) and (isinstance(id, Iterable) and
                                not isinstance(id, StringTypes)):
        webenv, query_key = webenv_post(db, id)
        id = None

    fetch_handle = Entrez.efetch(db=db, id=id,
                                 webenv=webenv, query_key=query_key)
    et = etree.parse(fetch_handle)
    fetch_handle.close()

    if out is not None:
        et.write(out)
    root = et.getroot()
    return root
