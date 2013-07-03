"""Simple class to encapsulate GData client for spreadsheets.

2013-06-10
Edward Liaw
"""
from __future__ import print_function
import sys
import os
import json
import urlparse
import gdata
from warnings import warn
from gdata.spreadsheet import service


class SimpleGData(object):
    """Encapsulated GData client for general purpose use of spreadsheets."""
    def __init__(self, email=None, pw=None):
        self.login(email, pw)
        self.sid = None
        self.wid = None

    @staticmethod
    def _query_feed(title):
        """Build a simple query for the title field in the document/worksheet
        xml."""
        q = service.DocumentQuery()
        q['title'] = title
        q['title-exact'] = 'true'
        return q

    @staticmethod
    def _entry_id(entry):
        split = urlparse.urlsplit(entry.id.text)
        return os.path.basename(split.path)
        #return entry.id.text.rsplit('/', 1)[1]

    @staticmethod
    def _feed_ids(feed):
        return [SimpleGData._entry_id(entry) for entry in feed.entry]

    @staticmethod
    def _feed_dict(feed):
        return {entry.title.text: SimpleGData._entry_id(entry) for entry in feed.entry}

    @staticmethod
    def _row_to_dict(row):
        return {key: row.custom[key].text for key in row.custom}

    @staticmethod
    def _feed_to_dict(feed):
        return [SimpleGData._row_to_dict(row) for row in feed.entry]

    def _feed(self):
        if self.sid is not None:
            if self.wid is None:
                return self.client.GetSpreadsheetsFeed(self.sid)
            else:
                return self.client.GetWorksheetsFeed(self.sid, self.wid)

    def login(self, email=None, pw=None):
        """Login a client using a Google email and password."""
        client = service.SpreadsheetsService()

        if email is None:
            client.email = raw_input('Google email: ')
        else:
            client.email = email
        if pw is None:
            client.password = raw_input('Google secret: ')
        else:
            client.password = pw

        try:
            client.ProgrammaticLogin()
            self.client = client
        except gdata.service.BadAuthentication:
            warn("Login failed.")

    def select_document(self, document):
        """Sets self.sid."""
        q = self._query_feed(document)
        feed = self.client.GetSpreadsheetsFeed(query=q)
        try:
            self.sid = self._feed_ids(feed)[0]
        except IndexError:
            warn("Could not find document")

    def select_worksheet(self, worksheet):
        """Sets self.wid."""
        if self.sid is None:
            warn("Need to select a spreadsheet first.")
            return

        q = self._query_feed(worksheet)
        feed = self.client.GetWorksheetsFeed(self.sid, query=q)
        try:
            self.wid = self._feed_ids(feed)[0]
        except IndexError:
            warn("Could not find worksheet.")

    def get_row_feed(self):
        if self.sid is None or self.wid is None:
            warn("Need to select a worksheet first.")
            return
        return self.client.GetListFeed(self.sid, self.wid)

    def get_json(self):
        return self._feed_to_dict(self.get_row_feed())

    def update_row(self, row):
        for a_link in row.link:
            if a_link.rel == 'edit':
                self.client.Put(row, a_link.href, converter=gdata.spreadsheet.SpreadsheetsListFromString)

    def dump_json(self, outfile=sys.stdout):
        json_dict = self.get_json()
        print(json.dumps(json_dict, sort_keys=True,
                         indent=2), file=outfile)
