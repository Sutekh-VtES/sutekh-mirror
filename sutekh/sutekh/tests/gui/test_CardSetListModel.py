# test_CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.gui.CardSetListModel import CardSetCardListModel, \
        NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, \
        EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS
from sutekh.core.Groupings import NullGrouping
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCard, \
        IExpansion, IAbstractCard
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

    # pylint: disable-msg=R0201
    # I prefer to have these as methods
    def _count_second_level(self, oModel):
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

    def _get_all_child_counts(self, oModel, oIter):
        """Recursively descend the children of oIter, getting all the
           relevant info."""
        aList = []
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            aList.append((oModel.get_card_count_from_iter(oChildIter),
                oModel.get_parent_count_from_iter(oChildIter),
                oModel.get_name_from_iter(oChildIter)))
            if oModel.iter_n_children(oChildIter) > 0:
                aList.extend(self._get_all_child_counts(oModel, oChildIter))
            oChildIter = oModel.iter_next(oChildIter)
        aList.sort()
        return aList

    def _get_all_counts(self, oModel):
        """Return a list of iCnt, iParCnt, sCardName tuples from the Model"""
        return self._get_all_child_counts(oModel, None)

    def _gen_card(self, sName, sExp):
        """Create a card given the name and Expansion"""
        if sExp:
            oExp = IExpansion(sExp)
        else:
            oExp = None
        oAbs = IAbstractCard(sName)
        return IPhysicalCard((oAbs, oExp))

    # pylint: enable-msg=R0201


    def test_basic(self):
        """Set of simple tests of the Card Set List Model"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables

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
        # Check for the 'No cards' entry in the model
        self.assertEquals(oModel.iter_n_children(None), 1)
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition')]
        for sName, sExp in aCards:
            oPhysCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oPhysCard.id)
        oModel.load()
        self.assertEqual(len(oListener.aCards), 2)
        # Only Vampires added
        self.assertEqual(oModel.iter_n_children(None), 1)
        oModel.groupby = NullGrouping
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 2)
        # Check the drag-n-drop helper
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0:0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                {'Camarilla Edition' : 1})
        self.assertEqual(oModel.get_drag_info_from_path('0:0:0'),
                (u"Alexandra", "Camarilla Edition", 1, 2))
        self.assertEqual(oModel.get_drag_info_from_path('0:0'),
                (u"Alexandra", None, 1, 1))
        self.assertEqual(oModel.get_drag_info_from_path('0'),
                (None, None, 2, 0))
        oModel.iExtraLevelsMode = NO_SECOND_LEVEL
        oModel.load()
        # This should also work for no expansions shown
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 0)
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                {'Camarilla Edition' : 1})
        # Add Cards
        # We don't repeat anything so we can use removePhysicalCard
        # successfully below
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')]
        aPhysCards = []
        for sName, sExp in aCards:
            oPhysCard = self._gen_card(sName, sExp)
            aPhysCards.append(oPhysCard)
        for iLevelMode in [NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, \
                        EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS]:
            oModel.iExtraLevelsMode = iLevelMode
            # pylint: disable-msg=E1101
            # SQLObjext confuses pylint
            oModel.load()
            for oCard in aPhysCards:
                oPCS.addPhysicalCard(oCard.id)
                oPCS.syncUpdate()
                oModel.inc_card(oCard)
            tAddTotals = (self._count_all_cards(oModel),
                    self._count_second_level(oModel))
            aList1 = self._get_all_counts(oModel)
            oModel.load()
            tTotals = (self._count_all_cards(oModel),
                    self._count_second_level(oModel))
            aList2 = self._get_all_counts(oModel)
            self.assertEqual(tAddTotals, tTotals, "inc_card and load differ,"
                    " %s vs %s when using mode %d" % (tAddTotals, tTotals,
                        iLevelMode))
            self.assertEqual(aList1, aList2, "inc_card and load differ, "
                    " %s vs %s, for mode %d" % (aList1, aList2, iLevelMode))
            # Card removal
            for oCard in aPhysCards:
                oPCS.removePhysicalCard(oCard.id)
                oPCS.syncUpdate()
                oModel.dec_card(oCard)
            tAddTotals = (self._count_all_cards(oModel),
                    self._count_second_level(oModel))
            aList1 = self._get_all_counts(oModel)
            oModel.load()
            tTotals = (self._count_all_cards(oModel),
                    self._count_second_level(oModel))
            aList2 = self._get_all_counts(oModel)
            self.assertEqual(tAddTotals, tTotals, "dec_card and load differ,"
                    " %s vs %s when using mode %d" % (tAddTotals, tTotals,
                        iLevelMode))
            self.assertEqual(aList1, aList2, "inc_card and load differ, "
                    " %s vs %s, for mode %d" % (aList1, aList2, iLevelMode))
            # Also test that we've behaved sanely
            self.assertEqual(self._count_all_cards(oModel), 2)
        aCards = [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oPhysCard = self._gen_card(sName, sExp)
            aPhysCards.append(oPhysCard)
        for iLevelMode in [NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, \
                        EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS]:
            # Test adding a repeated card
            # pylint: disable-msg=E1101
            # SQLObjext confuses pylint
            oModel.iExtraLevelsMode = iLevelMode
            oModel.load()
            for oCard in aPhysCards:
                oPCS.addPhysicalCard(oCard.id)
                oPCS.syncUpdate()
                oModel.inc_card(oCard)
            aList1 = self._get_all_counts(oModel)
            oModel.load()
            aList2 = self._get_all_counts(oModel)
            self.assertEqual(aList1, aList2, "inc_card and load differ, "
                    " %s vs %s, for mode %d" % (aList1, aList2, iLevelMode))
            # remove the cards
            for oCard in set(aPhysCards):
                oPCS.removePhysicalCard(oCard.id)
            oPCS.syncUpdate()
            oModel.load()
            # sanity checks
            # We drop to one, since we've removed all Alexandra's
            self.assertEqual(self._count_all_cards(oModel), 1)
            if iLevelMode == SHOW_EXPANSIONS:
                self.assertEqual(self._count_second_level(oModel), 1)
        # FIXME: Test the rest of the functionality
        # Test addition + deletion with parent card set, sibling card set
        # and child card sets
        # Test adding cards + removing card from parent card sets, child
        # card sets and siblings
        # Test filtering with the different modes

if __name__ == "__main__":
    unittest.main()
