# test_LackeyDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an Lackey CCG deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.LackeyDeckParser import LackeyDeckParser

LACKEY_EXAMPLE_1 = """
2\tTest Card 1
4\tTest Card 2
12\tTest Card 3
1\tTest Card 4
1\tPath of Blood, The
Crypt:
2\tTest Vamp 1
1\tLazar Dobrescu
1\tAlan Sovereign Adv.
"""


# Needs to be a SutekhTestCase so the name mapping cache test works
class TestLackeyDeckFileParser(SutekhTest):
    """class for the ELDB deck file parser tests"""

    def test_basic(self):
        """Run the input test."""
        oHolder = self._make_holder_from_string(LackeyDeckParser(),
                LACKEY_EXAMPLE_1)

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 8)
        self.failUnless(("Test Vamp 1", 2) in aCards)
        self.failUnless((u"L\xe1z\xe1r Dobrescu", 1) in aCards)
        self.failUnless(("Test Card 1", 2) in aCards)
        self.failUnless(("Test Card 2", 4) in aCards)
        self.failUnless(("Test Card 3", 12) in aCards)
        self.failUnless(("Test Card 4", 1) in aCards)
        self.failUnless(("Alan Sovereign (Advanced)", 1) in aCards)
        self.failUnless(("The Path of Blood", 1) in aCards)

if __name__ == "__main__":
    unittest.main()
