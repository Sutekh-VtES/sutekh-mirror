# __init__.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This is the sutekh test suite"""

from sutekh.core.SutekhObjects import TABLE_LIST, VersionTable
from sutekh.SutekhUtility import read_white_wolf_list, read_rulings, \
        refresh_tables
from sutekh.tests.TestData import TEST_CARD_LIST, TEST_RULINGS
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.WwFile import WwFile
from sqlobject import sqlhub, connectionForURI
import tempfile
import os
from logging import FileHandler


def _create_pkg_tmp_file(sData):
    """Create a temporary file for use in create_db"""
    (fTemp, sFilename) = tempfile.mkstemp()
    os.close(fTemp)

    if sData:
        fTmp = file(sFilename, "wb")
        fTmp.write(sData)
        fTmp.close()

    return sFilename


def create_db():
    """Create the database"""
    assert refresh_tables(TABLE_LIST, sqlhub.processConnection)

    sCardList = _create_pkg_tmp_file(TEST_CARD_LIST)
    sRulings = _create_pkg_tmp_file(TEST_RULINGS)

    oLogHandler = FileHandler('/dev/null')
    read_white_wolf_list([WwFile(sCardList)], oLogHandler)
    read_rulings([WwFile(sRulings)], oLogHandler)

    os.remove(sRulings)
    os.remove(sCardList)


def setup_package():
    """Fill database before any of the tests are run"""
    # Get the database to use from the environment, defaulting to an
    # sqlite memory DB
    sDBUrl = os.getenv('SUTEKH_TEST_DB', "sqlite:///:memory:")
    oConn = connectionForURI(sDBUrl)
    sqlhub.processConnection = oConn
    SutekhTest.set_db_conn(oConn)

    create_db()


def teardown_package():
    """Cleanup the database after all the tests are done"""
    sSaveDB = os.getenv('SUTEKH_SAVE_DB', "No").lower()
    if sSaveDB != 'yes':
        for cCls in reversed(TABLE_LIST):
            cCls.dropTable(ifExists=True)
        VersionTable.dropTable(ifExists=True)
