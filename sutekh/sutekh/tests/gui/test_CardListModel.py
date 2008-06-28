# test_CardListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard
from sutekh.core import Filters, Groupings
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
        while oIter:
            oChildIter = oModel.iter_children(oIter)
            while oChildIter:
                iTotal += oModel.iter_n_children(oChildIter)
                oChildIter = oModel.iter_next(oChildIter)
            oIter = oModel.iter_next(oIter)
        return iTotal

    def _count_all_cards(self, oModel):
        """Count all the card entries in the model."""
        iTotal = 0
        oIter = oModel.get_iter_first()
        while oIter:
            iTotal += oModel.iter_n_children(oIter)
            oIter = oModel.iter_next(oIter)
        return iTotal

    def _count_top_level(self, oModel):
        """Count all the top level enterie in the model."""
        iTotal = oModel.iter_n_children(None)
        return iTotal

    # pylint: enable-msg=R0201

    def test_basic(self):
        """Set of simple tests of the Card List Model"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        oModel = CardListModel()
        oListener = TestListener()
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)
        oModel.add_listener(oListener)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        aExpectedCards = set(AbstractCard.select())
        self.assertEqual(aExpectedCards, set(oListener.aCards))
        self.assertEqual(oModel.get_card_iterator(None).count(),
                PhysicalCard.select().count())
        # The model as an entry for every AbstractCard and entries
        # below that for every PhysicalCard
        # Set grouping to None for these tests
        oModel.groupby = Groupings.NullGrouping
        oModel.load()
        self.assertEqual(self._count_all_cards(oModel),
                AbstractCard.select().count())
        self.assertEqual(self._count_expansions(oModel),
                PhysicalCard.select().count())
        # Check without expansions
        oModel.bExpansions = False
        oModel.load()
        self.assertEqual(self._count_all_cards(oModel),
                AbstractCard.select().count())
        self.assertEqual(self._count_expansions(oModel), 0)
        oModel.bExpansions = True
        oModel.groupby = Groupings.CryptLibraryGrouping
        oModel.load()
        self.assertEqual(self._count_all_cards(oModel),
                AbstractCard.select().count())
        self.assertEqual(self._count_expansions(oModel),
                PhysicalCard.select().count())
        self.assertEqual(self._count_top_level(oModel), 2)
        # Test filtering
        # Test filter which selects nothing works
        oModel.selectfilter = Filters.CardNameFilter('ZZZZZZZ')
        oModel.applyfilter = True
        oModel.load()
        self.assertEqual(self._count_top_level(oModel), 1)
        self.assertEqual(self._count_all_cards(oModel), 0)
        oModel.applyfilter = False
        oModel.load()
        self.assertEqual(self._count_all_cards(oModel),
                AbstractCard.select().count())
        self.assertEqual(self._count_expansions(oModel),
                PhysicalCard.select().count())
        self.assertEqual(self._count_top_level(oModel), 2)
        # Test card type
        oModel.selectfilter = Filters.CardTypeFilter('Vampire')
        oModel.applyfilter = True
        oModel.load()
        self.assertEqual(self._count_top_level(oModel), 1)
        self.assertEqual(self._count_expansions(oModel),
                oModel.get_card_iterator(oModel.selectfilter).count())
        oModel.groupby = Groupings.CardTypeGrouping
        oModel.load()
        self.assertEqual(self._count_top_level(oModel), 1)
        self.assertEqual(self._count_expansions(oModel),
                oModel.get_card_iterator(oModel.selectfilter).count())
        # Test path queries
        oPath = '0:0:0' # First expansion for the first card
        self.assertEqual(oModel.get_exp_name_from_path(oPath),
                oModel.sUnknownExpansion)
        self.assertEqual(oModel.get_card_name_from_path(oPath),
                u'Aabbt Kindred')
        tAll = oModel.get_all_from_path(oPath)
        self.assertEqual(tAll[0], u'Aabbt Kindred')
        self.assertEqual(tAll[1], oModel.sUnknownExpansion)
        self.assertEqual(tAll[2], 0)
        self.assertEqual(tAll[3], 2)
        self.assertEqual(oModel.get_child_entries_from_path(oPath), [])
        oPath = '0:0' # First card
        self.assertEqual(oModel.get_exp_name_from_path(oPath), None)
        self.assertEqual(oModel.get_inc_dec_flags_from_path(oPath),
                (False, False))
        tAll = oModel.get_all_from_path(oPath)
        self.assertEqual(tAll[0], u'Aabbt Kindred')
        self.assertEqual(tAll[1], None)
        self.assertEqual(tAll[2], 0)
        self.assertEqual(tAll[3], 1)
        self.assertEqual(oModel.get_child_entries_from_path(oPath),
                [(oModel.sUnknownExpansion, 0), ('Final Nights', 0)])

        oListener.bLoadCalled = False
        oModel.remove_listener(oListener)
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)

if __name__ == "__main__":
    unittest.main()
