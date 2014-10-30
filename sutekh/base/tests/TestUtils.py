# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2008, 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# _iterdump():
#   Copyright 2008 Python Software Foundation; All Rights Reserved
# GPL - see COPYING for details

"""Utilities and support classes that are useful for testing."""

import unittest
import tempfile
import os
import sys
import StringIO
import gtk
from nose import SkipTest
from logging import FileHandler


def create_tmp_file(sDir, sData):
    """Create a temporary file in the given directory."""
    (fTemp, sFilename) = tempfile.mkstemp(dir=sDir)
    os.close(fTemp)

    if sData:
        fTmp = open(sFilename, "wb")
        fTmp.write(sData)
        fTmp.close()

    return sFilename


def create_pkg_tmp_file(sData):
    """Create a temporary file for use in package setup."""
    return create_tmp_file(None, sData)


class BaseTestCase(unittest.TestCase):
    """Base class for tests.

       Define some useful helper methods.
       """
    # pylint: disable=R0904
    # R0904 - unittest.TestCase, so many public methods

    TEST_CONN = None
    PREFIX = 'testcase'

    @classmethod
    def set_db_conn(cls, oConn):
        """Set the class connection to the correct global conn for later use"""
        cls.TEST_CONN = oConn

    def _create_tmp_file(self, sData=None):
        """Creates a temporary file with the given data, closes it and returns
           the filename."""
        sFilename = create_tmp_file(self._sTempDir, sData)
        self._aTempFiles.append(sFilename)

        return sFilename

    # pylint: disable=C0103, W0201
    # C0103: setUp + tearDown names are needed by unittest, so we use
    #        their conventions
    # W0201: _setUpTemps is called from setUp, so defining things here OK
    def _setUpTemps(self):
        """Create a directory to hold the temporary files."""
        self._sTempDir = tempfile.mkdtemp(suffix='dir', prefix=self.PREFIX)
        self._aTempFiles = []

    def _tearDownTemps(self):
        """Clean up the temporary files."""
        for sFile in self._aTempFiles:
            if os.path.exists(sFile):
                # Tests may clean up their own temp files
                os.remove(sFile)
        os.rmdir(self._sTempDir)
        self._sTempDir = None
        self._aTempFiles = None
    # pylint: enable=C0103, W0201

    def _round_trip_obj(self, oWriter, oObj):
        """Round trip an object through a temporary file.

           Common operation for the writer tests."""
        sTempFile = self._create_tmp_file()
        fOut = open(sTempFile, 'w')
        oWriter.write(fOut, oObj)
        fOut.close()

        fIn = open(sTempFile, 'rU')
        sData = fIn.read()
        fIn.close()
        return sData

    # pylint: disable=R0201
    # method for consistency with _round_trip_obj
    def _make_holder_from_string(self, oParser, sString):
        """Read the given string into a DummyHolder.

           common operation for the parser tests"""
        oHolder = DummyHolder()
        oParser.parse(StringIO.StringIO(sString), oHolder)
        return oHolder


class DummyHolder(object):
    """Emulate CardSetHolder for test purposes."""
    def __init__(self):
        self.dCards = {}
        # pylint: disable=C0103
        # placeholder names for CardSetHolder attributes
        self.name = ''
        self.comment = ''
        self.author = ''
        self.annotations = ''

    def add(self, iCnt, sName, sExpName):
        """Add a card to the dummy holder."""
        self.dCards.setdefault((sName, sExpName), 0)
        self.dCards[(sName, sExpName)] += iCnt

    def get_cards_exps(self):
        """Get the cards with expansions"""
        return self.dCards.items()

    def get_cards(self):
        """Get the card info without expansions"""
        dNoExpCards = {}
        for sCardName, sExpName in self.dCards:
            dNoExpCards.setdefault(sCardName, 0)
            dNoExpCards[sCardName] += self.dCards[(sCardName, sExpName)]
        return dNoExpCards.items()


class GuiBaseTest(unittest.TestCase):
    """Adds useful methods for gui test cases."""

    # pylint: disable=C0103, R0904
    # C0103 - setUp + tearDown names are needed by unittest,
    #         so use their convention
    # R0904 - unittest.TestCase, so many public methods

    def setUp(self):
        """Check if we should run the gui tests."""
        # Skip if we're not under a windowing system
        # We need to do this before trying to run MainWindows's __init__,
        # which will fail if not under a windowing system
        if gtk.gdk.screen_get_default() is None:
            raise SkipTest
        # avoid menu proxy stuff on Ubuntu
        os.environ["UBUNTU_MENUPROXY"] = "0"
        super(GuiBaseTest, self).setUp()

    def tearDown(self):
        """Cleanup gtk state after test."""
        # Process pending gtk events so cleanup completes
        while gtk.events_pending():
            gtk.main_iteration()
        super(GuiBaseTest, self).tearDown()


def make_null_handler():
    """Utility function to create a logger for /dev/null that works
       on both windows and Linux"""
    if sys.platform.startswith("win"):
        return FileHandler('NUL')
    return FileHandler('/dev/null')


def _iterdump(connection):
    """
    # From Python 3.0
    # Mimic the sqlite3 console shell's .dump command
    # Author: Paul Kippes <kippesp@gmail.com>

    Returns an iterator to the dump of the database in an SQL text format.

    Used to produce an SQL dump of the database.  Useful to save an in-memory
    database for later restoration.  This function should not be called
    directly but instead called from the Connection method, iterdump().
    """
    # pylint: disable=C0103
    # Using the original naming convention

    cu = connection.cursor()
    # yield('BEGIN TRANSACTION;')

    # sqlite_master table contains the SQL CREATE statements for the database.
    q = """
        SELECT name, type, sql
        FROM sqlite_master
            WHERE sql NOT NULL AND
            type == 'table'
        """
    schema_res = cu.execute(q)
    # pylint: disable-msg=W0612
    # W0612: _type and _name are unused, by don't match our conventions
    # due to matching original naming
    for table_name, _type, sql in schema_res.fetchall():
        if table_name == 'sqlite_sequence':
            yield('DELETE FROM sqlite_sequence;')
        elif table_name == 'sqlite_stat1':
            yield('ANALYZE sqlite_master;')
        elif table_name.startswith('sqlite_'):
            continue
        # NOTE: Virtual table support not implemented
        #elif sql.startswith('CREATE VIRTUAL TABLE'):
        #    qtable = table_name.replace("'", "''")
        #    yield("INSERT INTO sqlite_master(type,name,tbl_name,rootpage,sql)"
        #        "VALUES('table','%s','%s',0,'%s');" %
        #        qtable,
        #        qtable,
        #        sql.replace("''"))
        else:
            yield('%s;' % sql)

        # Build the insert statement for each row of the current table
        res = cu.execute("PRAGMA table_info('%s')" % table_name)
        column_names = [str(table_info[1]) for table_info in res.fetchall()]
        q = "SELECT 'INSERT INTO \"%(tbl_name)s\" VALUES("
        q += ",".join(["'||quote(" + col + ")||'" for col in column_names])
        q += ")' FROM '%(tbl_name)s'"
        query_res = cu.execute(q % {'tbl_name': table_name})
        for row in query_res:
            yield("%s;" % row[0])
    # pylint: enable-msg=W0612

    # Now when the type is 'index', 'trigger', or 'view'
    q = """
        SELECT name, type, sql
        FROM sqlite_master
            WHERE sql NOT NULL AND
            type IN ('index', 'trigger', 'view')
        """
    schema_res = cu.execute(q)
    # pylint: disable-msg=W0612
    # see above
    for _name, _type, sql in schema_res.fetchall():
        yield('%s;' % sql)
    # pylint: enable-msg=W0612

    # yield('COMMIT;')
