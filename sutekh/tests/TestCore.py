# TestCore.py
# -*- coding: utf8 -*-
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.tests.TestData import TEST_CARD_LIST, TEST_RULINGS
from sutekh.SutekhUtility import readWhiteWolfList, readRulings, refreshTables
from sutekh.core.SutekhObjects import ObjectList
from sqlobject import sqlhub, connectionForURI
import unittest
import tempfile
import os

class SutekhTest(unittest.TestCase):
    def _createTmpFile(self,sData=None):
        """Creates a temporary file with the given data, closes it and returns
           the filename."""
        (fd, sFilename) = tempfile.mkstemp(dir=self._sTempDir)
        os.close(fd)
        self._aTempFiles.append(sFilename)

        if sData:
            fTmp = file(sFilename,"wb")
            fTmp.write(sData)
            fTmp.close()

        return sFilename

    def _setUpTemps(self):
        self._sTempDir = tempfile.mkdtemp(suffix='dir',prefix='sutekhtests')
        self._aTempFiles = []

    def _tearDownTemps(self):
        for sFile in self._aTempFiles:
            os.remove(sFile)
        os.rmdir(self._sTempDir)
        self._sTempDir = None
        self._aTempFiles = None

    def setUp(self):
        self._setUpTemps()

        sCardList = self._createTmpFile(TEST_CARD_LIST)
        sRulings = self._createTmpFile(TEST_RULINGS)

        oConn = connectionForURI("sqlite:///:memory:")
        sqlhub.processConnection = oConn

        assert refreshTables(ObjectList, oConn)

        readWhiteWolfList(sCardList)
        readRulings(sRulings)

    def tearDown(self):
        sqlhub.processConnection = None
        self._tearDownTemps()
