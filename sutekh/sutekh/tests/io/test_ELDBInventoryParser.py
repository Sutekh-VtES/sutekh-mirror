# test_ELDBInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ELDB inventory file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.ELDBInventoryParser import ELDBInventoryParser

class DummyHolder(object):
    """Emulate CardSetHolder for test purposes."""
    def __init__(self):
        self.dCards = {}
        # pylint: disable-msg=C0103
        # placeholder names for CardSetHolder attributes
        self.name = ''
        self.comment = ''
        self.author = ''

    # pylint: disable-msg=W0613
    # sExpName is unused, but needed to make function signature match
    def add(self, iCnt, sName, sExpName):
        """Add a card to the dummy holder."""
        self.dCards.setdefault(sName, 0)
        self.dCards[sName] += iCnt


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

        aCards = oHolder.dCards.items()

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
