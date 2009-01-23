# test_LackeyDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an Lackey CCG deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest, DummyHolder
from sutekh.io.LackeyDeckParser import LackeyDeckParser

# Needs to be a SutekhTestCase so the name mapping cache test works
class TestLackeyDeckFileParser(SutekhTest):
    """class for the ELDB deck file parser tests"""

    sTestText1 = """
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

    def test_basic(self):
        """Run the input test."""
        oHolder = DummyHolder()
        oParser = LackeyDeckParser(oHolder)

        for sLine in self.sTestText1.split("\n"):
            oParser.feed(sLine + "\n")

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 8)
        self.failUnless(("Test Vamp 1", 2) in aCards)
        self.failUnless((u"L\xe1z\xe1r Dobrescu", 1) in aCards)
        self.failUnless(("Test Card 1", 2 ) in aCards)
        self.failUnless(("Test Card 2", 4) in aCards)
        self.failUnless(("Test Card 3", 12) in aCards)
        self.failUnless(("Test Card 4", 1) in aCards)
        self.failUnless(("Alan Sovereign (Advanced)", 1) in aCards)
        self.failUnless(("The Path of Blood", 1) in aCards)

if __name__ == "__main__":
    unittest.main()
