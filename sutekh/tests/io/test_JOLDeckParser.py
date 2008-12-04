# test_JOLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an JOL deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest, DummyHolder
from sutekh.io.JOLDeckParser import JOLDeckParser

class TestJOLDeckParser(SutekhTest):
    """class for the JOL deck file parser tests"""

    sTestText1 = """
        3xTest Vamp 1
        Test Vamp 2
        Test Card 1
        Test Card 1
        4xTest Card 2
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
        """

    def test_basic(self):
        """Run the JOL input test."""
        oHolder = DummyHolder()
        oParser = JOLDeckParser(oHolder)

        for sLine in self.sTestText1.split("\n"):
            oParser.feed(sLine + "\n")

        aCards = oHolder.get_cards()

        print aCards
        self.assertEqual(len(aCards), 6)
        self.failUnless(("Test Vamp 1", 3) in aCards)
        self.failUnless(("Test Vamp 2", 1) in aCards)
        self.failUnless(("Test Card 1", 2 ) in aCards)
        self.failUnless(("Test Card 2", 4) in aCards)
        self.failUnless(("Test Card 3", 12) in aCards)
        self.failUnless(("Test Card 4", 1) in aCards)

if __name__ == "__main__":
    unittest.main()
