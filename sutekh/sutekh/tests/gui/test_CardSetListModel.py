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
        EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS, \
        THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS, CHILD_CARDS, \
        IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, MINUS_SETS_IN_USE
from sutekh.core.Groupings import NullGrouping, ClanGrouping, \
        DisciplineGrouping, ExpansionGrouping, RarityGrouping, \
        CryptLibraryGrouping, CardTypeGrouping
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCard, \
        IExpansion, IAbstractCard, MapPhysicalCardToPhysicalCardSet
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

    aParentCountToStr = ['IGNORE_PARENT', 'PARENT_COUNT', 'MINUS_THIS_SET',
            'MINUS_SETS_IN_USE']
    aExtraLevelToStr = ['NO_SECOND_LEVEL', 'SHOW_EXPANSIONS', 'SHOW_CARD_SETS',
            'EXPANSIONS_AND_CARD_SETS', 'CARD_SETS_AND_EXPANSIONS']
    aCardCountToStr = ['THIS_SET_ONLY', 'ALL_CARDS', 'PARENT_CARDS',
            'CHILD_CARDS']

    # pylint: disable-msg=R0201
    # I prefer to have these as methods
    def _count_second_level(self, oModel):
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
        """Count all the entries in the model."""
        iTotal = 0
        oIter = oModel.get_iter_first()
        while oIter:
            iTotal += oModel.iter_n_children(oIter)
            oIter = oModel.iter_next(oIter)
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

    def _format_error(self, sErrType, oTest1, oTest2, oModel):
        """Format an informative error message"""
        # pylint: disable-msg=W0212
        # Need info from _oCardSet here
        sModel = "Model: [card set %s, inuse=%s, groupby=%s]\n" % (
                    oModel._oCardSet.name, oModel._oCardSet.inuse,
                    oModel.groupby)
        sModel += " State : (ExtraLevelsMode %s, ParentCountMode : %s, " \
                "ShowCardMode : %s, Editable: %s)" % (
                        self.aExtraLevelToStr[oModel.iExtraLevelsMode],
                        self.aParentCountToStr[oModel.iParentCountMode],
                        self.aCardCountToStr[oModel.iShowCardMode],
                        oModel.bEditable)
        return "%s : %s vs %s\n%s" % (sErrType, oTest1, oTest2, sModel)

    def _gen_card_signal(self, oPCS, oModel, oPhysCard, iDir):
        """Generate the approriate message to the Model.

           Very similiar to the logic in CardSetController."""
        # pylint: disable-msg=W0212
        # Need info from _oCardSet here
        oModelPCS = oModel._oCardSet
        if oPCS.id == oModelPCS.id:
            if iDir > 0:
                oModel.inc_card(oPhysCard)
            else:
                oModel.dec_card(oPhysCard)
        elif oPCS.parent and oPCS.parent.id == oModelPCS.id and \
                oModel.changes_with_children() and oPCS.inuse:
            # Child card set changing
            if iDir > 0:
                oModel.inc_child_count(oPhysCard, oPCS.name)
            else:
                oModel.dec_child_count(oPhysCard, oPCS.name)
        elif oModelPCS.parent and oModelPCS.parent.id == oPCS.id and \
                oModel.changes_with_parent():
            # Parent card set changing
            if iDir > 0:
                oModel.inc_parent_count(oPhysCard)
            else:
                oModel.dec_parent_count(oPhysCard)
        elif oModelPCS.parent and oPCS.parent and oPCS.inuse and \
                oPCS.parent.id == oModelPCS.parent.id and \
                oModel.changes_with_siblings():
            # Sibling card set to the model
            if iDir > 0:
                oModel.inc_sibling_count(oPhysCard)
            else:
                oModel.dec_sibling_count(oPhysCard)


    # pylint: enable-msg=R0201

    def _add_remove_distinct_cards(self, oPCS, oModel):
        """Helper function to add and remove distinct cards from the card set,
           validating that the model works correctly"""
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')]
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            aPhysCards.append(oCard)
        # pylint: disable-msg=E1101
        # SQLObjext confuses pylint
        oModel.load()
        iStart = self._count_all_cards(oModel)
        for oCard in aPhysCards:
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            self._gen_card_signal(oPCS, oModel, oCard, 1)
        tAlterTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        tTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList2 = self._get_all_counts(oModel)
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for inc_card and load differ", tAlterTotals, tTotals,
            oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card Lists for inc_card and load differ", aList1, aList2,
            oModel))
        # Card removal
        # We use the map table, so we can also test dec_card properly
        for oCard in aPhysCards:
            oMapEntry = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, physicalCardSetID=oPCS.id))[-1]
            MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
            oPCS.syncUpdate()
            self._gen_card_signal(oPCS, oModel, oCard, -1)
        tAlterTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        tTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList2 = self._get_all_counts(oModel)
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for dec_card and load differ", tAlterTotals, tTotals,
            oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card lists for dec_card and load differ", aList1, aList2, oModel))
        # Also test that we've behaved sanely
        iEnd = self._count_all_cards(oModel)
        self.assertEqual(iEnd, iStart, self._format_error(
            "Card set differs from start after removals", iEnd, iStart,
            oModel))

    def _add_remove_repeated_cards(self, oPCS, oModel):
        """Helper function to add and remove repeated cards from the card set,
           validating that the model works correctly"""
        aCards = [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            aPhysCards.append(oCard)
        oModel.load()
        iStart = self._count_all_cards(oModel)
        for oCard in aPhysCards:
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            self._gen_card_signal(oPCS, oModel, oCard, 1)
        tAlterTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        aList2 = self._get_all_counts(oModel)
        tTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for repeated inc_card and load differ", tAlterTotals,
            tTotals, oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card lists for repeated inc_card and load differ, ", aList1,
            aList2, oModel))
        for oCard in aPhysCards:
            oMapEntry = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, physicalCardSetID=oPCS.id))[-1]
            MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
            oPCS.syncUpdate()
            self._gen_card_signal(oPCS, oModel, oCard, -1)
        tAlterTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aList1 = self._get_all_counts(oModel)
        oModel.load()
        aList2 = self._get_all_counts(oModel)
        tTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        self.assertEqual(tAlterTotals, tTotals, self._format_error(
            "Totals for repeated dec_card and load differ", tAlterTotals,
            tTotals, oModel))
        self.assertEqual(aList1, aList2, self._format_error(
            "Card lists for repeated dec_card and load differ, ", aList1,
            aList2, oModel))
        # sanity checks
        iEnd = self._count_all_cards(oModel)
        self.assertEqual(iEnd, iStart, self._format_error(
            "Card set differs from start after removals", iEnd, iStart,
            oModel))

    def _loop_modes(self, oPCS, oModel):
        """Loop over all the possible modes of the model, calling
           _add_remove_cards to test the model."""
        for bEditFlag in [False, True]:
            oModel.bEditable = bEditFlag
            for iLevelMode in [NO_SECOND_LEVEL, SHOW_EXPANSIONS,
                    SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS,
                    CARD_SETS_AND_EXPANSIONS]:
                oModel.iExtraLevelsMode = iLevelMode
                for iParentMode in [IGNORE_PARENT, PARENT_COUNT,
                        MINUS_THIS_SET, MINUS_SETS_IN_USE]:
                    oModel.iParentCountMode = iParentMode
                    for iShowMode in [THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS,
                            CHILD_CARDS]:
                        oModel.iShowCardMode = iShowMode
                        self._add_remove_distinct_cards(oPCS, oModel)
                        self._add_remove_repeated_cards(oPCS, oModel)

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
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
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
        self._loop_modes(oPCS, oModel)
        # Check over all the groupings
        for cGrouping in [CryptLibraryGrouping, RarityGrouping,
                ExpansionGrouping, DisciplineGrouping, ClanGrouping,
                CardTypeGrouping]:
            oModel.groupby = cGrouping
            self._loop_modes(oPCS, oModel)
        oModel.groupby = NullGrouping
        # Add some more cards
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
        # Create a child card set with some entries and check everything works
        sName2 = 'Test Child 1'
        sName3 = 'Test Grand Child'
        sName4 = 'Test Sibling'
        sName5 = 'Test Grand Child 2'
        oChildPCS = PhysicalCardSet(name=sName2, parent=oPCS)
        oChildModel = CardSetCardListModel(sName2)
        for sName, sExp in aCards[2:6]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChildPCS.addPhysicalCard(oCard.id)
        oChildModel.groupby = NullGrouping
        oChildModel.load()
        oChildPCS.inuse = False
        # Check adding cards when we have a parent card set
        self._loop_modes(oChildPCS, oChildModel)
        # Check adding cards when we have a child, but no parent
        self._loop_modes(oPCS, oModel)
        # And when we're in use
        oChildPCS.inuse = True
        self._loop_modes(oChildPCS, oChildModel)
        self._loop_modes(oPCS, oModel)
        # Add a grand child
        oGrandChildPCS = PhysicalCardSet(name=sName3, parent=oChildPCS)
        for sName, sExp in aCards[3:7]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oGrandChildPCS.addPhysicalCard(oCard.id)
        oGrandChildPCS.inuse = False
        # Check adding cards when we have a parent card set and a child
        self._loop_modes(oChildPCS, oChildModel)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, oChildModel)
        # Add some cards to oGrandChildPCS that aren't in parent and oChildPCS,
        # add a sibling card set to oChildPCS and add another child and retest
        oSibPCS = PhysicalCardSet(name=sName4, parent=oPCS)
        for sName, sExp in aCards[1:6]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oSibPCS.addPhysicalCard(oCard.id)
        oSibPCS.inus = True
        oGrandChild2PCS = PhysicalCardSet(name=sName5, parent=oChildPCS)
        oGrandChild2PCS.inuse = True
        aCards = [('AK-47', 'LotN'), ('Cesewayo', 'LoB'),
                ('Aire of Elation', 'CE'), ('Yvette, The Hopeless', None),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oGrandChild2PCS.addPhysicalCard(oCard.id)
            if sName == 'Aire of Elation':
                oGrandChildPCS.addPhysicalCard(oCard.id)
                oGrandChildPCS.addPhysicalCard(oCard.id)
                oGrandChildPCS.addPhysicalCard(oCard.id)
                oGrandChildPCS.syncUpdate()
            oGrandChild2PCS.syncUpdate()
        oGrandChildPCS.inuse = False
        self._loop_modes(oChildPCS, oChildModel)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, oChildModel)
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        oGrandChild2PCS.addPhysicalCard(self._gen_card('Ablative Skin',
            'Sabbat'))
        self._loop_modes(oChildPCS, oChildModel)
        oChildPCS.addPhysicalCard(self._gen_card('Ablative Skin',
            'Sabbat'))
        oGrandChild2PCS.addPhysicalCard(self._gen_card(
            'Ablative Skin', None))
        self._loop_modes(oChildPCS, oChildModel)
        oGCModel = CardSetCardListModel(sName3)
        # Test adding cards to a sibling card set
        self._loop_modes(oGrandChild2PCS, oGCModel)
        self._loop_modes(oSibPCS, oChildModel)
        # Test adding cards to the parent card set
        self._loop_modes(oPCS, oChildModel)
        self._loop_modes(oChildPCS, oGCModel)
        # Test adding cards to the child card set
        self._loop_modes(oChildPCS, oModel)
        self._loop_modes(oSibPCS, oModel)
        self._loop_modes(oGrandChildPCS, oChildModel)
        # Go through the grouping tests as well
        for cGrouping in [CryptLibraryGrouping, RarityGrouping,
                ExpansionGrouping, DisciplineGrouping, ClanGrouping,
                CardTypeGrouping]:
            oChildModel.groupby = cGrouping
            self._loop_modes(oSibPCS, oChildModel)
            self._loop_modes(oPCS, oChildModel)
            self._loop_modes(oGrandChildPCS, oChildModel)
        # FIXME: Test filtering with the different modes

if __name__ == "__main__":
    unittest.main()
