# TestCore.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# _iterdump():
#   Copyright 2008 Python Software Foundation; All Rights Reserved
# Remainder:
#   Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base for Sutekh test cases"""

from sutekh.SutekhUtility import refresh_tables
from sutekh.core.SutekhObjects import PHYSICAL_SET_LIST
from sqlobject import sqlhub
import unittest
import tempfile
import os
import StringIO


class SutekhTest(unittest.TestCase):
    """Base class for Sutekh tests.

       Define common setup and teardown routines common to test cases.
       """

    TEST_CONN = None

    @classmethod
    def set_db_conn(cls, oConn):
        """Set the class connection to the correct global conn for later use"""
        cls.TEST_CONN = oConn

    def _create_tmp_file(self, sData=None):
        """Creates a temporary file with the given data, closes it and returns
           the filename."""
        (fTemp, sFilename) = tempfile.mkstemp(dir=self._sTempDir)
        os.close(fTemp)
        self._aTempFiles.append(sFilename)

        if sData:
            fTmp = file(sFilename, "wb")
            fTmp.write(sData)
            fTmp.close()

        return sFilename

    # pylint: disable-msg=C0103
    # setUp + tearDown names are needed by unittest - use their convention
    # pylint: disable-msg=W0201
    # setUp is always called by the tests, so it doesn't matter that
    # declarations aren't in __init__
    def _setUpTemps(self):
        """Create a directory to hold the temporary files."""
        self._sTempDir = tempfile.mkdtemp(suffix='dir', prefix='sutekhtests')
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

    # pylint: disable-msg=R0201
    # This is a method for convience
    def _setUpDb(self):
        """Initialises a database with the cardlist and
           rulings.
           """
        assert refresh_tables(PHYSICAL_SET_LIST, sqlhub.processConnection)

    # pylint: enable-msg=R0201

    def setUp(self):
        """Common setup routine for tests.

           Initialises a database with the cardlist and rulings.
           """
        self._setUpTemps()
        self._setUpDb()

    def tearDown(self):
        """Common teardown routine for tests.

           Base sqlite cleanup.
           """
        self._tearDownTemps()
        # Undo any connection fiddling
        sqlhub.processConnection = self.TEST_CONN

    def _round_trip_obj(self, oWriter, oObj):
        """Round trip an object through a temporary file.

           Common operation for the writer tests."""
        sTempFile = self._create_tmp_file()
        fOut = file(sTempFile, 'w')
        oWriter.write(fOut, oObj)
        fOut.close()

        fIn = open(sTempFile, 'rU')
        sData = fIn.read()
        fIn.close()
        return sData

    # pylint: disable-msg=R0201
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
        # pylint: disable-msg=C0103
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
    # pylint: disable-msg=C0103
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

    # Now when the type is 'index', 'trigger', or 'view'
    q = """
        SELECT name, type, sql
        FROM sqlite_master
            WHERE sql NOT NULL AND
            type IN ('index', 'trigger', 'view')
        """
    schema_res = cu.execute(q)
    for _name, _type, sql in schema_res.fetchall():
        yield('%s;' % sql)

    # yield('COMMIT;')
