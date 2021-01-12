# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This is the sutekh test suite"""

import pytest

from sqlobject import sqlhub

from sutekh.base.core.BaseTables import PHYSICAL_SET_LIST
from sutekh.base.core.DBUtility import refresh_tables

from sutekh.tests import setup_package, teardown_package


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
    """Cleanup the database after a test run"""
    assert refresh_tables(PHYSICAL_SET_LIST, sqlhub.processConnection)
