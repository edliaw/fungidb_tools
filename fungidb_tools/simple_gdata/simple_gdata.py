"""Simple class to encapsulate GData client for spreadsheets.

2013-06-10
Edward Liaw
"""
from __future__ import print_function
import os
import json
import urlparse
import gdata
from warnings import warn
from gdata.spreadsheet import service


class GDataException(Exception):
    pass


def _entry_id(entry):
    """Pull out the GData ID from a url."""
    split = urlparse.urlsplit(entry.id.text)
    return os.path.basename(split.path)


def _entry_ids(feed):
    """Get a list of IDs from an XML feed."""
    return [_entry_id(entry) for entry in feed.entry]


def _entries_dict(feed):
    """Get a list of IDs as a dictionary of {document titles : ID}."""
    return {entry.title.text: _entry_id(entry) for entry in feed.entry}


def _row_to_dict(row):
    """Convert XML fields for a list feed into a dictionary."""
    return {key: row.custom[key].text for key in row.custom}


def _jsonize_list_feed(feed):
    """Turn a list feed into a JSON-like object."""
    return [_row_to_dict(row) for row in feed.entry]


def _query_feed(title):
    """Build a simple query for the title field in the document/worksheet
    xml."""
    q = service.DocumentQuery()
    q['title'] = title
    q['title-exact'] = 'true'
    return q


class SimpleGData(object):
    """Encapsulated GData client for general purpose use of spreadsheets."""
    def __init__(self, email, pw):
        client = service.SpreadsheetsService()
        client.email = email
        client.password = pw
        client.ProgrammaticLogin()
        self.client = client
        self._sid = None
        self._wid = None

    @classmethod
    def prompt_creds(cls, email=None, pw=None):
        """Login using a Google email and password."""
        if email is None:
            email = raw_input('Google email: ')
        if pw is None:
            pw = raw_input('Google secret: ')
        return cls(email, pw)

    @property
    def sid(self):
        """The document ID."""
        if self._sid is None:
            raise GDataException("Document ID not set.")
        return self._sid

    @sid.setter
    def sid(self, document_id):
        self._sid = document_id

    @property
    def wid(self):
        """The worksheet ID."""
        if self._wid is None:
            raise GDataException("Worksheet ID not set.")
        return self._wid

    @wid.setter
    def wid(self, worksheet_id):
        if self._sid is None:
            raise GDataException("Must select a document before selecting a "
                                 "worksheet.")
        self._wid = worksheet_id

    def select_document(self, name):
        """Select a document by name."""
        feed = self.client.GetSpreadsheetsFeed(query=_query_feed(name))
        try:
            self.sid = _entry_ids(feed)[0]
        except IndexError:
            warn("Could not find document %s." % name)

    def select_worksheet(self, name):
        """Choose a spreadsheet by name."""
        feed = self.client.GetWorksheetsFeed(self.sid, query=_query_feed(name))
        try:
            self.wid = _entry_ids(feed)[0]
        except IndexError:
            warn("Could not find worksheet %s." % name)

    def get_list_feed(self):
        """Get the rows of the spreadsheet as an XML feed."""
        return self.client.GetListFeed(self.sid, self.wid)

    def json_feed(self):
        """Get the rows of the spreadsheet as a JSON-like object."""
        return _jsonize_list_feed(self.get_list_feed())

    def json_dump(self):
        """Dump out the spreadsheet rows as a JSON string."""
        json_dict = self.json_feed()
        return json.dumps(json_dict, sort_keys=True, indent=2)

    def update_row(self, row):
        """Update a row (XML GData object)."""
        for a_link in row.link:
            if a_link.rel == 'edit':
                self.client.Put(row, a_link.href, converter=gdata.spreadsheet.SpreadsheetsListFromString)

    def _feed(self):
        try:
            return self.client.GetWorksheetsFeed(self.sid, self.wid)
        except GDataException:
            return self.client.GetSpreadsheetsFeed(self.sid)
