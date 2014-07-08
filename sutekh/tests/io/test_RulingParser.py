# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test the Sutekh ruling parser"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.base.core.BaseObjects import Ruling, IRuling
import unittest


class RulingParserTests(SutekhTest):
    """Check the results of the ruling parser call in SutekhTest SetUp"""
    # pylint: disable-msg=R0904
    # R0904 - unittest.TestCase, so many public methods
    aExpectedRulings = [
        u"[LSJ 19990215]", u"[LSJ 19990216]", u"[LSJ 20070928]",
    ]

    def test_basic(self):
        """Basic test method for ruling parser tests."""
        aRulings = sorted(list(Ruling.select()), key=lambda oR: oR.code)

        self.assertEqual([oR.code for oR in aRulings], self.aExpectedRulings)

        oRuling = aRulings[0]
        self.failUnless(oRuling.text.startswith(u"Cannot use his "))

        oRuling = aRulings[1]
        self.failUnless(oRuling.text.startswith(u"Cannot be used "))

        oRuling = aRulings[2]
        self.failUnless(oRuling.text.startswith(u"The AK-47 provides "))

        # pylint: disable-msg=E1101
        # IRuling confuses pylint
        oRuling = IRuling((aRulings[0].text, aRulings[0].code))
        self.assertEqual(oRuling.code, self.aExpectedRulings[0])
        self.assertNotEqual(oRuling.url, None)

if __name__ == "__main__":
    unittest.main()
