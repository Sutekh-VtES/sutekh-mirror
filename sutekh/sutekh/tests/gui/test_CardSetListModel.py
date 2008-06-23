# test_CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.gui.CardSetListModel import CardSetCardListModel
from sutekh.core.SutekhObjects import PhysicalCardSet
import unittest

class CardSetListener(CardListModelListener):
    """Listener used in the test cases."""
    # pylint: disable-msg=W0231
    # CardListModelListener has no __init__
    def __init__(self):
        self.bLoadCalled = False
        self.aCards = []

    def load(self, aAbsCards):
        """Called when the model is loaded."""
        self.bLoadCalled = True
        self.aCards = aAbsCards

class CardSetListModelTests(SutekhTest):
    """Class for the test cases"""

    def test_basic(self):
        """Set of simple tests of the Card List Model"""
        sName = 'Test 1'
        oPCS = PhysicalCardSet(name=sName)
        oModel = CardSetCardListModel(sName)
        oListener = CardSetListener()
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)
        oModel.add_listener(oListener)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        self.assertEquals(len(oListener.aCards), 0)
        # FIXME: Test the rest of the functionality

if __name__ == "__main__":
    unittest.main()
