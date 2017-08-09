# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base for Sutekh test cases"""

from sutekh.base.core.DBUtility import refresh_tables
from sutekh.base.core.BaseObjects import PHYSICAL_SET_LIST
from sutekh.base.tests.TestUtils import BaseTestCase
from sqlobject import sqlhub


class SutekhTest(BaseTestCase):
    """Base class for Sutekh tests.

       Define common setup and teardown routines common to test cases.
       """
    # pylint: disable=R0904
    # R0904 - unittest.TestCase, so many public methods

    PREFIX = 'sutekhtests'

    # pylint: disable=C0103
    # setUp + tearDown names are needed by unittest - use their convention
    # pylint: disable=W0201
    # setUp is always called by the tests, so it doesn't matter that
    # declarations aren't in __init__
    # pylint: disable=R0201
    # This is a method for convience
    def _setUpDb(self):
        """Initialises a database with the cardlist and
           rulings.
           """
        assert refresh_tables(PHYSICAL_SET_LIST, sqlhub.processConnection)

    # pylint: enable=R0201

    def setUp(self):
        """Common setup routine for tests.

           Initialises a database with the cardlist and rulings.
           """
        self._setUpTemps()
        self._setUpDb()
        super(SutekhTest, self).setUp()

    def tearDown(self):
        """Common teardown routine for tests.

           Base sqlite cleanup.
           """
        self._tearDownTemps()
        # Undo any connection fiddling
        sqlhub.processConnection = self.TEST_CONN
        super(SutekhTest, self).tearDown()
