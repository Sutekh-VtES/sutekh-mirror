# test_RulingParser.py
# -*- coding: utf8 -*-
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.io.ARDBTextParser import ARDBTextParser
import unittest

class DummyHolder(object):
    def __init__(self):
        self.aCards = []

    def add(self,iCnt,sName):
        self.aCards.append((iCnt,sName))

class ARDBTextParserTests(unittest.TestCase):
    sTestText = """
        Deck Name : Test Deck
        Author : Anon Y Mous
        Description :
        Simple test deck.

        http://www.example.url/in/description

        Crypt [3 vampires] Capacity min: 2 max: 10 average: 7.33
       ------------------------------------------------------------
        2x Test Vamp 1			  10 ...
        1x Test Vamp 2			  2  ...
        ...

        Library [19 cards]
        ------------------------------------------------------------
        Action [6]
            2x Test Card 1
            4x Test Card 2

        Action Modifier [12]
            12x Test Card 3

        Reaction [1]
            1x Test Card 4
        ...
    """

    def testBasic(self):
        oH = DummyHolder()
        oP = ARDBTextParser(oH)

        for sLine in self.sTestText.split("\n"):
            oP.feed(sLine + "\n")

        self.assertEqual(oH.name,"Test Deck")
        self.assertEqual(oH.author,"Anon Y Mous")
        self.failUnless(oH.comment.startswith("        Simple test deck."))
        self.failUnless(oH.comment.endswith("in/description\n\n"))

        aCards = oH.aCards

        self.assertEqual(len(aCards),6)
        self.failUnless((2,"Test Vamp 1") in aCards)
        self.failUnless((1,"Test Vamp 2") in aCards)
        self.failUnless((2,"Test Card 1") in aCards)
        self.failUnless((4,"Test Card 2") in aCards)
        self.failUnless((12,"Test Card 3") in aCards)
        self.failUnless((1,"Test Card 4") in aCards)

if __name__ == "__main__":
    unittest.main()
