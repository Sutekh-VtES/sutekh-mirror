# test_RulingParser.py
# -*- coding: utf8 -*-
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import Ruling, IRuling
import unittest

class RulingParserTests(SutekhTest):
    aExpectedRulings = [
        u"[LSJ19990215]", u"[LSJ19990216]", u"[LSJ20070928]",
    ]

    def testBasic(self):
        aRulings = sorted(list(Ruling.select()),cmp=lambda oR1,oR2: cmp(oR1.code,oR2.code))

        self.assertEqual([oR.code for oR in aRulings],self.aExpectedRulings)

        oR = aRulings[0]
        self.failUnless(oR.text.startswith(u"Cannot use his "))

        oR = aRulings[1]
        self.failUnless(oR.text.startswith(u"Cannot be used "))

        oR = aRulings[2]
        self.failUnless(oR.text.startswith(u"The AK-47 provides "))

        oR = IRuling((aRulings[0].text,aRulings[0].code))
        self.assertEqual(oR.code,self.aExpectedRulings[0])

if __name__ == "__main__":
    unittest.main()
