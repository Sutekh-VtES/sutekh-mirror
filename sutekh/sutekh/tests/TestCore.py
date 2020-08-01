# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Base for Sutekh test cases"""

import pytest
from sqlobject import sqlhub

from sutekh.base.tests.TestUtils import BaseTestCase


@pytest.mark.usefixtures("db_setup", "clean_db")
class SutekhTest(BaseTestCase):
    """Base class for Sutekh tests.

       Define common setup and teardown routines common to test cases.
       """
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    PREFIX = 'sutekhtests'

    # pylint: disable=invalid-name
    # setUp + tearDown names are needed by unittest - use their convention

    def setUp(self):
        """Common setup routine for tests.

           Initialises a database with the cardlist and rulings.
           """
        self._setUpTemps()
        super().setUp()

    def tearDown(self):
        """Common teardown routine for tests.

           Base sqlite cleanup.
           """
        self._tearDownTemps()
        # Undo any connection fiddling
        sqlhub.processConnection = self.TEST_CONN
        super().tearDown()
