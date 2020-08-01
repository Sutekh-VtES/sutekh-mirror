# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This is the sutekh test suite"""

import os

import pytest

from sqlobject import sqlhub, connectionForURI

from sutekh.base.core.BaseTables import VersionTable, PHYSICAL_SET_LIST
from sutekh.base.core.DBUtility import refresh_tables
from sutekh.base.io.EncodedFile import EncodedFile
from sutekh.base.tests.TestUtils import make_null_handler, create_pkg_tmp_file

from sutekh.SutekhUtility import (read_white_wolf_list, read_rulings,
                                  read_exp_info_file, read_lookup_data)
from sutekh.core.SutekhTables import TABLE_LIST
from sutekh.tests.TestData import (TEST_CARD_LIST, TEST_RULINGS,
                                   TEST_EXP_INFO, TEST_LOOKUP_LIST)
from sutekh.tests.TestCore import SutekhTest

from sutekh.tests import create_db, setup_package, teardown_package


@pytest.fixture(scope='session')
def db_setup():
    """Fill database before any of the tests are run"""
    # Get the database to use from the environment, defaulting to an
    # sqlite memory DB
    setup_package()
    yield sqlhub.processConnection
    teardown_package()


@pytest.fixture(scope='function')
def clean_db():
    assert refresh_tables(PHYSICAL_SET_LIST, sqlhub.processConnection)

