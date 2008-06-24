# test_CardListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard
from sutekh.core.Groupings import NullGrouping
from sutekh.gui.CardListModel import CardListModel, CardListModelListener
import unittest

class TestListener(CardListModelListener):
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

class CardListModelTests(SutekhTest):
    """Class for the test cases"""

    # pylint: disable-msg=R0201
    # I prefer to have these as methods
    def _count_expansions(self, oModel):
        """Count all the second level entries in the model."""
        iTotal = 0
        oIter = oModel.get_iter_first()
        # We assume grouping is NullGrouping here
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            iTotal += oModel.iter_n_children(oChildIter)
            oChildIter = oModel.iter_next(oChildIter)
        return iTotal

    def _count_all_cards(self, oModel):
        """Count all the entries in the model."""
        iTotal = 0
        # We assume grouping is NullGrouping here
        oIter = oModel.get_iter_first()
        iTotal = oModel.iter_n_children(oIter)
        return iTotal

    # pylint: enable-msg=R0201

    def test_basic(self):
        """Set of simple tests of the Card List Model"""
        oModel = CardListModel()
        oListener = TestListener()
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)
        oModel.add_listener(oListener)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        aExpectedCards = set(AbstractCard.select())
        self.assertEqual(aExpectedCards, set(oListener.aCards))
        # The model as an entry for every AbstractCard and entries
        # below that for every PhysicalCard
        # Set grouping to None for these tests
        oModel.groupby = NullGrouping
        oModel.load()
        self.assertEqual(self._count_all_cards(oModel),
                AbstractCard.select().count())
        self.assertEqual(self._count_expansions(oModel),
                PhysicalCard.select().count())
        # FIXME: Test the rest of the functionality

if __name__ == "__main__":
    unittest.main()
