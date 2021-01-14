# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2021 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for various Utility functions"""

import datetime
import unittest


from sutekh.base.Utility import (normalise_whitespace, move_articles_to_back,
                                 move_articles_to_front, get_expansion_date,
                                 get_printing_date)
from sutekh.base.core.BaseAdapters import IExpansion, IPrinting, IAbstractCard
from sutekh.SutekhUtility import  find_base_vampire, find_adv_vampire
from sutekh.tests.TestCore import SutekhTest


class MiscUtilityTests(SutekhTest):
    """class for the Card Set Utility tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_name_transforms(self):
        """Test various name / text transforms"""
        # Check that the article transforms correctly
        def roundtrip1(sString):
            return move_articles_to_front(move_articles_to_back(sString))

        def roundtrip2(sString):
            return move_articles_to_back(move_articles_to_front(sString))

        self.assertEqual(move_articles_to_back('AAAA'), 'AAAA')
        self.assertEqual(move_articles_to_back('There'), 'There')
        self.assertEqual(move_articles_to_front('AAAA'), 'AAAA')
        self.assertEqual(move_articles_to_front('There'), 'There')
        # Check moving articles
        self.assertEqual(move_articles_to_back('A thing'), 'thing, A')
        self.assertEqual(move_articles_to_back('An another'), 'another, An')
        self.assertEqual(move_articles_to_back('The ra ra ra'),
                         'ra ra ra, The')
        # Check moves reverse correctly
        self.assertEqual(roundtrip1('A thing'), 'A thing')
        self.assertEqual(roundtrip1('An another'), 'An another')
        self.assertEqual(roundtrip1('The ra ra ra'), 'The ra ra ra')

        self.assertEqual(roundtrip2('thing, A'), 'thing, A')
        self.assertEqual(roundtrip2('another, An'), 'another, An')
        self.assertEqual(roundtrip2('ra ra ra, The'), 'ra ra ra, The')

    def test_normalise(self):
        """Check that normalise whitespace does the right thing"""

        self.assertEqual(normalise_whitespace('A A A'), 'A A A')
        self.assertEqual(normalise_whitespace('A   A   A'), 'A A A')
        self.assertEqual(normalise_whitespace('A\n A\nA'), 'A A A')
        self.assertEqual(normalise_whitespace('A\tA\t\t\tA'), 'A A A')

    def test_printing_date(self):
        """Test getting the printing date functions"""
        # VtES is not given a date in the test data, so this works
        self.assertEqual(get_expansion_date(IExpansion('VTES')), None)
        self.assertEqual(get_expansion_date(IExpansion('Jyhad')),
                         datetime.date(year=1994, month=8, day=16))
        self.assertEqual(get_expansion_date(IExpansion('SW')),
                         datetime.date(year=2000, month=10, day=31))

        VtES = IPrinting((IExpansion('VTES'), None))
        SWfirst = IPrinting((IExpansion('SW'), None))
        SWsecond = IPrinting((IExpansion('SW'), 'Second Printing'))

        self.assertEqual(get_printing_date(VtES), None)
        self.assertEqual(get_printing_date(SWfirst),
                         datetime.date(year=2000, month=10, day=31))
        self.assertEqual(get_printing_date(SWsecond),
                         datetime.date(year=2001, month=1, day=12))

    def test_find_vamps(self):
        """Test functions for finding base/adv vampires."""
        oAlanBase = IAbstractCard('Alan Sovereign')
        oNewBlood = IAbstractCard('New Blood')
        oAlanAdv = IAbstractCard('Alan Sovereign (Advanced)')

        self.assertEqual(find_base_vampire(oAlanAdv), oAlanBase)

        self.assertEqual(find_adv_vampire(oAlanBase), oAlanAdv)
        self.assertEqual(find_adv_vampire(oNewBlood), None)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
