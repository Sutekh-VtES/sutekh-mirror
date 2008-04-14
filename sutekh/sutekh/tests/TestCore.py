# TestCore.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base for Sutekh test cases"""

from sutekh.tests.TestData import TEST_CARD_LIST, TEST_RULINGS
from sutekh.SutekhUtility import read_white_wolf_list, read_rulings, \
        refresh_tables
from sutekh.core.SutekhObjects import aObjectList
from sutekh.io.WwFile import WwFile
from sqlobject import sqlhub, connectionForURI
import unittest
import tempfile
import os
from logging import FileHandler

class SutekhTest(unittest.TestCase):
    """Base class for Sutekh tests.

       Define common setup and teardown routines common to test cases.
       """

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
            os.remove(sFile)
        os.rmdir(self._sTempDir)
        self._sTempDir = None
        self._aTempFiles = None

    def setUp(self):
        """Common setup routine for tests.

           Initialises a sqlite memory database with the cardlist and
           rulings.
           """
        self._setUpTemps()

        sCardList = self._create_tmp_file(TEST_CARD_LIST)
        sRulings = self._create_tmp_file(TEST_RULINGS)

        oConn = connectionForURI("sqlite:///:memory:")
        sqlhub.processConnection = oConn

        assert refresh_tables(aObjectList, oConn)

        oLogHandler = FileHandler('/dev/null')
        read_white_wolf_list(WwFile(sCardList), oLogHandler)
        read_rulings(WwFile(sRulings), oLogHandler)

    def tearDown(self):
        """Common teardown routine for tests.

           Base sqlite cleanup.
           """
        sqlhub.processConnection = None
        self._tearDownTemps()
