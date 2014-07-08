# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This is the sutekh test suite"""

from sutekh.core.SutekhObjects import TABLE_LIST
from sutekh.base.core.BaseObjects import VersionTable
from sutekh.SutekhUtility import read_white_wolf_list, read_rulings
from sutekh.base.core.DBUtility import refresh_tables
from sutekh.tests.TestData import TEST_CARD_LIST, TEST_RULINGS
from sutekh.tests.TestCore import SutekhTest
from sutekh.base.tests.TestUtils import make_null_handler, create_pkg_tmp_file
from sutekh.base.io.EncodedFile import EncodedFile
from sqlobject import sqlhub, connectionForURI
import os


def create_db():
    """Create the database"""
    assert refresh_tables(TABLE_LIST, sqlhub.processConnection)

    sCardList = create_pkg_tmp_file(TEST_CARD_LIST)
    sRulings = create_pkg_tmp_file(TEST_RULINGS)

    oLogHandler = make_null_handler()
    read_white_wolf_list([EncodedFile(sCardList)], oLogHandler)
    read_rulings([EncodedFile(sRulings)], oLogHandler)

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
