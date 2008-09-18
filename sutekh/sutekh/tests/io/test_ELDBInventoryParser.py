# test_ELDBInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ELDB inventory file"""

import unittest
from sutekh.tests.TestCore import SutekhTest, DummyHolder
from sutekh.io.ELDBInventoryParser import ELDBInventoryParser

# Needs to be a SutekhTestCase so the name mapping cache test works
class TestELDBInventoryParser(SutekhTest):
    """class for the ELDB inventory reading test"""

    sTestText1 = """
        "ELDB - Inventory"
        "Test Vamp 1",2,0,"","Crypt"
        "Lazar Dobrescu",1,0,"","Crypt"
        "Test Vamp 2",0,0,"","Crypt"
        "Test Card 1",2,0,"","Library"
        "Test Card 2",4,0,"","Library"
        "Test Card 3",12,0,"","Library"
        "Test Card 4",1,0,"","Library"
        "Test Card 5",0,0,"","Library"
        """
        # FELD creates 0,0 entries, so they need to be in the test case

    def test_basic(self):
        """Run the input test."""
        oHolder = DummyHolder()
        oParser = ELDBInventoryParser(oHolder)

        for sLine in self.sTestText1.split("\n"):
            oParser.feed(sLine + "\n")

        self.assertEqual(oHolder.name, "")

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 6)
        self.failUnless(("Test Vamp 1", 2) in aCards)
        self.failUnless((u"L\xe1z\xe1r Dobrescu", 1) in aCards)
        self.failUnless(("Test Card 1", 2 ) in aCards)
        self.failUnless(("Test Card 2", 4) in aCards)
        self.failUnless(("Test Card 3", 12) in aCards)
        self.failUnless(("Test Card 4", 1) in aCards)
        # We don't need to test that the 0,0 entries have been skipped, as
        # that's covered by the len test

if __name__ == "__main__":
    unittest.main()
