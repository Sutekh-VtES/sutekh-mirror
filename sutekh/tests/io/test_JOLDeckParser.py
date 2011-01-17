# test_JOLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an JOL deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.JOLDeckParser import JOLDeckParser

JOL_EXAMPLE_1 = """
3xTest Vamp 1
Alan Sovereign (advanced)
The Path of Blood
Path of Blood, The
Test Vamp 2
Test Card 1
Test Card 1
4 x   Test Card 2
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 3
Test Card 4
12x Test Card 5
2 xTest Card 6
"""


class TestJOLDeckParser(SutekhTest):
    """class for the JOL deck file parser tests"""

    def test_basic(self):
        """Run the JOL input test."""
        oHolder = self._make_holder_from_string(JOLDeckParser(), JOL_EXAMPLE_1)

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 10)
        self.failUnless(("Test Vamp 1", 3) in aCards)
        self.failUnless(("Test Vamp 2", 1) in aCards)
        self.failUnless(("Test Card 1", 2) in aCards)
        self.failUnless(("Test Card 2", 4) in aCards)
        self.failUnless(("Test Card 3", 12) in aCards)
        self.failUnless(("Test Card 4", 1) in aCards)
        self.failUnless(("Test Card 5", 12) in aCards)
        self.failUnless(("Test Card 6", 2) in aCards)
        self.failUnless(("The Path of Blood", 2) in aCards)
        self.failUnless(("Alan Sovereign (Advanced)", 1) in aCards)

if __name__ == "__main__":
    unittest.main()
