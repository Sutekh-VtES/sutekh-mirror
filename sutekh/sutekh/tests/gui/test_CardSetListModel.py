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
from sutekh.core import Filters, Groupings
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCard, \
        IExpansion, IAbstractCard, MapPhysicalCardToPhysicalCardSet
# Needed to reduce speed impact of Grouping tests
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.core.DBSignals import send_changed_signal
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

    aNames = ['Test 1', 'Test Child 1', 'Test Grand Child', 'Test Sibling',
            'Test Grand Child 2']


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

    def _reset_modes(self, oModel):
        """Set the model to the minimal state."""
        # The database signal handling means that all CardSetListModels
        # associated with a card set will update when send_changed_signal is
        # called, so we reset the model state so these calls will be cheap if
        # this models is affected when we're not explicitly testing it.
        oModel.iParentCountMode = IGNORE_PARENT
        oModel.iLevelMode = NO_SECOND_LEVEL
        oModel.bEditable = False
        oModel.iShowMode = THIS_SET_ONLY

    # pylint: disable-msg=R0913
    # Need all these arguments here
    def _format_error(self, sErrType, oTest1, oTest2, oModel, oPCS=None):
        """Format an informative error message"""
        # pylint: disable-msg=W0212
        # Need info from _oCardSet here
        if oPCS:
            sModel = "Changing card set %s\n" % oPCS.name
        else:
            sModel = ''
        sModel += "Model: [card set %s, inuse=%s, groupby=%s]\n" % (
                    oModel._oCardSet.name, oModel._oCardSet.inuse,
                    oModel.groupby)
        sModel += " State : (ExtraLevelsMode %s, ParentCountMode : %s, " \
                "ShowCardMode : %s, Editable: %s)" % (
                        self.aExtraLevelToStr[oModel.iExtraLevelsMode],
                        self.aParentCountToStr[oModel.iParentCountMode],
                        self.aCardCountToStr[oModel.iShowCardMode],
                        oModel.bEditable)
        return "%s : %s vs %s\n%s" % (sErrType, oTest1, oTest2, sModel)

    # pylint: enable-msg=R0201
    # pylint: enable-msg=R0913

    def _add_remove_cards(self, oPCS, oModel, aPhysCards):
        """Helper function to add and remove distinct cards from the card set,
           validating that the model works correctly"""
        # pylint: disable-msg=E1101
        # SQLObjext confuses pylint
        oModel.sEditColour = "red"
        oModel.load()
        tStartTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aStartList = self._get_all_counts(oModel)
        for oCard in aPhysCards:
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, 1)
        tAddTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aAddList = self._get_all_counts(oModel)
        oModel.load()
        tLoadTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aLoadList = self._get_all_counts(oModel)
        self.assertEqual(tAddTotals, tLoadTotals, self._format_error(
            "Totals for inc_card and load differ", tAddTotals, tLoadTotals,
            oModel, oPCS))
        self.assertEqual(aAddList, aLoadList, self._format_error(
            "Card Lists for inc_card and load differ", aAddList, aLoadList,
            oModel, oPCS))
        # Card removal
        # We use the map table, so we can also test dec_card properly
        for oCard in aPhysCards:
            oMapEntry = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, physicalCardSetID=oPCS.id))[-1]
            MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, -1)
        tDecTotals = (
                oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        aDecList = self._get_all_counts(oModel)
        # test that we've behaved sanely
        self.assertEqual(tDecTotals, tStartTotals, self._format_error(
            "Totals for dec_card and load differ", tDecTotals, tStartTotals,
            oModel, oPCS))
        self.assertEqual(aDecList, aStartList, self._format_error(
            "Card lists for dec_card and load differ", aDecList, aStartList,
            oModel, oPCS))

    def _loop_modes(self, oPCS, oModel):
        """Loop over all the possible modes of the model, calling
           _add_remove_cards to test the model."""
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')] + [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            aPhysCards.append(oCard)
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
                        self._add_remove_cards(oPCS, oModel, aPhysCards)
        self._reset_modes(oModel)

    def _loop_zero_filter_modes(self, oModel):
        """Loop over all the possible modes of the model, calling
           a zero result filters to test the model."""
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
                        oModel.selectfilter = Filters.CardNameFilter('ZZZZZZZ')
                        oModel.applyfilter = True
                        oModel.load()
                        tFilterTotals = (
                                oModel.iter_n_children(None),
                                self._count_all_cards(oModel),
                                self._count_second_level(oModel))
                        self.assertEqual(tFilterTotals, (1, 0, 0),
                                self._format_error("Totals for filter differ"
                                    " from expected zero result",
                                    tFilterTotals, (1, 0, 0), oModel))

    def test_basic(self):
        """Set of simple tests of the Card Set List Model"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        # pylint: disable-msg=W0612
        # oCache exists only for the internal cache, so it's unused
        oCache = SutekhObjectCache()
        # pylint: enable-msg=W0612
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0])
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
        oModel.groupby = Groupings.NullGrouping
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
        self._reset_modes(oModel)
        self._loop_modes(oPCS, oModel)
        # Check over all the groupings
        for cGrouping in [Groupings.CryptLibraryGrouping,
                Groupings.DisciplineGrouping, Groupings.ClanGrouping,
                Groupings.CardTypeGrouping, Groupings.ExpansionGrouping,
                Groupings.RarityGrouping]:
            oModel.groupby = cGrouping
            self._loop_modes(oPCS, oModel)

    def test_relationships(self):
        """Tests Model against more complex Card Set relationships"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        # pylint: disable-msg=W0612
        # oCache exists only for the internal cache, so it's unused
        oCache = SutekhObjectCache()
        # pylint: enable-msg=W0612
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0])
        # Add cards
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
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
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        for sName, sExp in aCards[2:6]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChildPCS.addPhysicalCard(oCard.id)
        oChildPCS.inuse = False
        # Check adding cards when we have a parent card set
        self._loop_modes(oPCS, oModel)
        # Change model to other card set
        oModel.update_to_new_db(self.aNames[1])
        self._loop_modes(oChildPCS, oModel)
        # Check adding cards when we have a child, but no parent
        # And when we're in use
        oChildPCS.inuse = True
        self._loop_modes(oChildPCS, oModel)
        # change back
        oModel.update_to_new_db(self.aNames[0])
        self._loop_modes(oPCS, oModel)
        # Add a grand child
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        for sName, sExp in aCards[3:7]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oGrandChildPCS.addPhysicalCard(oCard.id)
        oGrandChildPCS.inuse = False
        # Check adding cards when we have a parent card set and a child
        oModel.update_to_new_db(self.aNames[1])
        self._loop_modes(oChildPCS, oModel)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, oModel)
        # Add some cards to oGrandChildPCS that aren't in parent and oChildPCS,
        # add a sibling card set to oChildPCS and add another child and retest
        oSibPCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS)
        for sName, sExp in aCards[1:6]:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oSibPCS.addPhysicalCard(oCard.id)
        oSibPCS.inuse = True
        oGrandChild2PCS = PhysicalCardSet(name=self.aNames[4],
                parent=oChildPCS)
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
        self._loop_modes(oChildPCS, oModel)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, oModel)
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        oGrandChild2PCS.addPhysicalCard(self._gen_card('Ablative Skin',
            'Sabbat'))
        self._loop_modes(oChildPCS, oModel)
        oChildPCS.addPhysicalCard(self._gen_card('Ablative Skin',
            'Sabbat'))
        oGrandChild2PCS.addPhysicalCard(self._gen_card(
            'Ablative Skin', None))
        self._loop_modes(oChildPCS, oModel)
        # Point model at grandchild
        oModel.update_to_new_db(self.aNames[2])
        # Test adding cards to a sibling card set
        self._loop_modes(oGrandChild2PCS, oModel)
        # point at child
        oModel.update_to_new_db(self.aNames[1])
        self._loop_modes(oSibPCS, oModel)
        # Test adding cards to the parent card set
        self._loop_modes(oPCS, oModel)
        # point at grand child
        oModel.update_to_new_db(self.aNames[2])
        self._loop_modes(oChildPCS, oModel)
        # Test adding cards to the child card set - point at parent
        oModel.update_to_new_db(self.aNames[0])
        self._loop_modes(oChildPCS, oModel)
        self._loop_modes(oSibPCS, oModel)
        # point at child
        oModel.update_to_new_db(self.aNames[1])
        self._loop_modes(oGrandChildPCS, oModel)
        # Go through some of grouping tests as well
        # We want to ensure that this works with non-NullGroupings,
        # but we don't need to cover all the groupings again
        for cGrouping in [Groupings.DisciplineGrouping,
                Groupings.CardTypeGrouping]:
            oModel.groupby = cGrouping
            self._loop_modes(oSibPCS, oModel)
            self._loop_modes(oPCS, oModel)
            self._loop_modes(oGrandChildPCS, oModel)

    def test_filters(self):
        """Test filtering for the card set"""
        # pylint: disable-msg=R0915
        # R0915: Want a long, sequential test case to reduce
        # repeated setups, so it has lots of lines
        # pylint: disable-msg=W0612
        # oCache exists only for the internal cache, so it's unused
        oCache = SutekhObjectCache()
        # pylint: enable-msg=W0612
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0])
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
        # Test filter which selects nothing works
        self._loop_zero_filter_modes(oModel)
        # Check basic filtering
        oModel.iShowCardMode = THIS_SET_ONLY
        oModel.iParentCountMode = IGNORE_PARENT
        oModel.iExtraLevelsMode = NO_SECOND_LEVEL
        oModel.bEditable = False
        oModel.groupby = Groupings.NullGrouping
        # Test card type
        oModel.selectfilter = Filters.CardTypeFilter('Vampire')
        oModel.applyfilter = True
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 4, 0)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel.groupby = Groupings.DisciplineGrouping
        oModel.applyfilter = True
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (11, 18, 0)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel.iExtraLevelsMode = SHOW_EXPANSIONS
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (11, 18, 25)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel.bEditable = True
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (11, 18, 48)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        # Add a child card set, and test filtering results
        oModel.groupby = Groupings.NullGrouping
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS,
                inuse=True)
        aCards = [('Sha-Ennu', None),
                ('Kabede Maru', None),
                ('Gracis Nostinus', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChildPCS.addPhysicalCard(oCard.id)
        oModel.bEditable = False
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 4, 6)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel.iExtraLevelsMode = SHOW_CARD_SETS
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 4, 2)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel.iShowCardMode = CHILD_CARDS
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 6, 4)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel.iShowCardMode = ALL_CARDS
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 26, 26)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))

    def test_empty(self):
        """Test corner cases around empty card sets"""
        # pylint: disable-msg=W0612
        # oCache exists only for the internal cache, so it's unused
        oCache = SutekhObjectCache()
        # pylint: enable-msg=W0612
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        oChildModel = CardSetCardListModel(self.aNames[1])
        oChildModel.groupby = Groupings.NullGrouping
        self._loop_modes(oChildPCS, oChildModel)
        self._loop_modes(oPCS, oChildModel)
        self._loop_modes(oGrandChildPCS, oChildModel)
        # Add some cards to parent + child card sets
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
            if sName != 'Yvette, The Hopeless':
                oGrandChildPCS.addPhysicalCard(oCard.id)
        self._loop_modes(oChildPCS, oChildModel)

if __name__ == "__main__":
    unittest.main()
