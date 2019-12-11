# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This is the sutekh test suite"""

import os

from sqlobject import sqlhub, connectionForURI

from sutekh.base.core.BaseTables import VersionTable
from sutekh.base.core.DBUtility import refresh_tables
from sutekh.base.io.EncodedFile import EncodedFile
from sutekh.base.tests.TestUtils import make_null_handler, create_pkg_tmp_file

from sutekh.SutekhUtility import (read_white_wolf_list, read_rulings,
                                  read_exp_info_file, read_lookup_data)
from sutekh.core.SutekhTables import TABLE_LIST
from sutekh.tests.TestData import (TEST_CARD_LIST, TEST_RULINGS,
                                   TEST_EXP_INFO, TEST_LOOKUP_LIST)
from sutekh.tests.TestCore import SutekhTest


def create_db():
    """Create the database"""
    assert refresh_tables(TABLE_LIST, sqlhub.processConnection)

    sLookupData = create_pkg_tmp_file(TEST_LOOKUP_LIST)
    sCardList = create_pkg_tmp_file(TEST_CARD_LIST)
    sRulings = create_pkg_tmp_file(TEST_RULINGS)
    sExpJSON = create_pkg_tmp_file(TEST_EXP_INFO)

    oLogHandler = make_null_handler()
    read_lookup_data(EncodedFile(sLookupData), oLogHandler)
    read_white_wolf_list(EncodedFile(sCardList), oLogHandler)
    read_exp_info_file(EncodedFile(sExpJSON), oLogHandler)
    read_rulings(EncodedFile(sRulings), oLogHandler)

    os.remove(sRulings)
    os.remove(sExpJSON)
    os.remove(sCardList)
    os.remove(sLookupData)


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
