# test_CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.gui.CardSetListModel import CardSetCardListModel
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
        # Add Cards
        # We don't repeat anything so we can use removePhysicalCard
        # successfully below
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')]
        for sName, sExp in aCards:
            oPhysCard = self._gen_card(sName, sExp)
            oPCS.addPhysicalCard(oPhysCard.id)
            oPCS.syncUpdate()
            oModel.inc_card(oPhysCard)
        iAddTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        oModel.load()
        iTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        self.assertEqual(iAddTotals, iTotals)
        # Card removal
        for sName, sExp in aCards:
            oPhysCard = self._gen_card(sName, sExp)
            oPCS.removePhysicalCard(oPhysCard.id)
            oPCS.syncUpdate()
            oModel.dec_card(oPhysCard)
        iAddTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        oModel.load()
        iTotals = (self._count_all_cards(oModel),
                self._count_second_level(oModel))
        self.assertEqual(iAddTotals, iTotals)
        # Also test that we've behaved sanely
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 2)
        # Test adding a repeated card
        aCards = [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        for sName, sExp in aCards:
            oPhysCard = self._gen_card(sName, sExp)
            oPCS.addPhysicalCard(oPhysCard.id)
            oPCS.syncUpdate()
            oModel.inc_card(oPhysCard)
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        aList2 = self._get_all_counts(oModel)
        self.assertEqual(aList1, aList2)
        # FIXME: Test the rest of the functionality

if __name__ == "__main__":
    unittest.main()
