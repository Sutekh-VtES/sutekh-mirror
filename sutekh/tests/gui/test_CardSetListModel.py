# test_CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Card List Model"""

from sutekh.tests.GuiSutekhTest import ConfigSutekhTest
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.gui.CardSetListModel import CardSetCardListModel, \
        NO_SECOND_LEVEL, SHOW_EXPANSIONS, SHOW_CARD_SETS, EXP_AND_CARD_SETS, \
        CARD_SETS_AND_EXP, ALL_CARDS, PARENT_CARDS, MINUS_SETS_IN_USE, \
        CHILD_CARDS, IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, THIS_SET_ONLY
from sutekh.core import Filters, Groupings
from sutekh.core.SutekhObjects import PhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.tests.core.test_Filters import make_card
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
        self.iCnt = 0

    def load(self, aCards):
        """Called when the model is loaded."""
        self.bLoadCalled = True
        self.iCnt = len(aCards)

    def alter_card_count(self, _oCard, iChg):
        """Called when the model alters the card count"""
        self.iCnt += iChg

    def add_new_card(self, _oCard, iCnt):
        """Called when the model adds a new card to the model"""
        self.iCnt += iCnt

class CardSetListModelTests(ConfigSutekhTest):
    """Class for the test cases"""

    aParentCountToStr = ['IGNORE_PARENT', 'PARENT_COUNT', 'MINUS_THIS_SET',
            'MINUS_SETS_IN_USE']
    aExtraLevelToStr = ['NO_SECOND_LEVEL', 'SHOW_EXPANSIONS', 'SHOW_CARD_SETS',
            'EXP_AND_CARD_SETS', 'CARD_SETS_AND_EXP']
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

    def _get_all_child_counts(self, oModel, oIter, sName=''):
        """Recursively descend the children of oIter, getting all the
           relevant info."""
        aList = []
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            if sName:
                sListName = sName + ':' + oModel.get_name_from_iter(oChildIter)
            else:
                sListName = oModel.get_name_from_iter(oChildIter)
            aList.append((oModel.get_card_count_from_iter(oChildIter),
                oModel.get_parent_count_from_iter(oChildIter), sListName))
            if oModel.iter_n_children(oChildIter) > 0:
                aList.extend(self._get_all_child_counts(oModel, oChildIter,
                    sListName))
            oChildIter = oModel.iter_next(oChildIter)
        aList.sort()
        return aList

    def _get_all_counts(self, oModel):
        """Return a list of iCnt, iParCnt, sCardName tuples from the Model"""
        return self._get_all_child_counts(oModel, None)

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

    def _cleanup_models(self, aModels):
        """Utility function to cleanup models signals, etc."""
        for oModel in aModels:
            oModel.cleanup()

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
        if oModel.applyfilter:
            sModel += "Filter: %s\n" % oModel.selectfilter
        sModel += " State : (ExtraLevelsMode %s, ParentCountMode : %s, " \
                "ShowCardMode : %s, Editable: %s)" % (
                        self.aExtraLevelToStr[oModel.iExtraLevelsMode],
                        self.aParentCountToStr[oModel.iParentCountMode],
                        self.aCardCountToStr[oModel.iShowCardMode],
                        oModel.bEditable)
        return "%s : %s vs %s\n%s" % (sErrType, oTest1, oTest2, sModel)

    # pylint: enable-msg=R0201
    # pylint: enable-msg=R0913

    # pylint: disable-msg=C0103
    # setUp + tearDown names are needed by unittest - use their convention
    def setUp(self):
        """Setup the card list used in _loop_modes"""
        super(CardSetListModelTests, self).setUp()
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')] + [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None), (u'Two Wrongs', None),
                (u'Agent of Power', None)] * 2
        self.aPhysCards = []
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            self.aPhysCards.append(oCard)

    # pylint: enable-msg=C0103

    def _add_remove_cards(self, oPCS, aModels):
        """Helper function to add and remove distinct cards from the card set,
           validating that the model works correctly"""
        # pylint: disable-msg=E1101, R0914
        # E1101: SQLObjext confuses pylint
        # R0914: several local variables, as we test a number of conditions
        dModelInfo = {}
        for oModel in aModels:
            oListener = CardSetListener()
            oModel.add_listener(oListener)
            oModel.sEditColour = "red"
            oModel.load()
            tStartTotals = (
                    oModel.iter_n_children(None),
                    self._count_all_cards(oModel),
                    self._count_second_level(oModel))
            aStartList = self._get_all_counts(oModel)
            dModelInfo[oModel] = [oListener, tStartTotals, aStartList]
        for oCard in self.aPhysCards:
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, 1)
        for oModel in aModels:
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
            iSetCnt = oModel.get_card_iterator(
                    oModel.get_current_filter()).count()
            iListCnt = dModelInfo[oModel][0].iCnt
            self.assertEqual(iListCnt, iSetCnt, self._format_error(
                "Listener has wrong count after inc_card", iListCnt,
                iSetCnt, oModel, oPCS))
        # Card removal
        # We use the map table, so we can also test dec_card properly
        for oCard in self.aPhysCards:
            oMapEntry = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, physicalCardSetID=oPCS.id))[-1]
            MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, -1)
        for oModel in aModels:
            tDecTotals = (
                    oModel.iter_n_children(None),
                    self._count_all_cards(oModel),
                    self._count_second_level(oModel))
            aDecList = self._get_all_counts(oModel)
            # test that we've behaved sanely
            oListener, tStartTotals, aStartList = dModelInfo[oModel]
            self.assertEqual(aDecList, aStartList, self._format_error(
                "Card lists for dec_card and load differ", aDecList,
                aStartList, oModel, oPCS))
            self.assertEqual(tDecTotals, tStartTotals, self._format_error(
                "Totals for dec_card and load differ", tDecTotals,
                tStartTotals, oModel, oPCS))
            iSetCnt = oModel.get_card_iterator(
                    oModel.get_current_filter()).count()
            self.assertEqual(oListener.iCnt, iSetCnt, self._format_error(
                "Listener has wrong count after inc_card", oListener.iCnt,
                iSetCnt, oModel, oPCS))
            oModel.remove_listener(oListener)

    def _loop_modes(self, oPCS, aModels):
        """Loop over all the possible modes of the model, calling
           _add_remove_cards to test the model."""
        for bEditFlag in [False, True]:
            for oModel in aModels:
                oModel.bEditable = bEditFlag
            for iLevelMode in [NO_SECOND_LEVEL, SHOW_EXPANSIONS,
                    SHOW_CARD_SETS, EXP_AND_CARD_SETS, CARD_SETS_AND_EXP]:
                for oModel in aModels:
                    oModel.iExtraLevelsMode = iLevelMode
                for iParentMode in [IGNORE_PARENT, PARENT_COUNT,
                        MINUS_THIS_SET, MINUS_SETS_IN_USE]:
                    for oModel in aModels:
                        oModel.iParentCountMode = iParentMode
                    for iShowMode in [THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS,
                            CHILD_CARDS]:
                        for oModel in aModels:
                            oModel.iShowCardMode = iShowMode
                        self._add_remove_cards(oPCS, aModels)
        for oModel in aModels:
            self._reset_modes(oModel)

    def _loop_zero_filter_modes(self, oModel):
        """Loop over all the possible modes of the model, calling
           a zero result filters to test the model."""
        for bEditFlag in [False, True]:
            oModel.bEditable = bEditFlag
            for iLevelMode in [NO_SECOND_LEVEL, SHOW_EXPANSIONS,
                    SHOW_CARD_SETS, EXP_AND_CARD_SETS, CARD_SETS_AND_EXP]:
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
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oListener = CardSetListener()
        oModel.load()
        self.assertFalse(oListener.bLoadCalled)
        oModel.add_listener(oListener)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        self.assertEquals(oListener.iCnt, 0)
        # Check for the 'No cards' entry in the model
        self.assertEquals(oModel.iter_n_children(None), 1)
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition')]
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
        oModel.load()
        self.assertEqual(oListener.iCnt, 2)
        # Only Vampires added
        self.assertEqual(oModel.iter_n_children(None), 1)
        oModel.groupby = Groupings.NullGrouping
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 2)
        # These tests need the model to be sorted
        oModel.enable_sorting()
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

    def _setup_simple(self):
        """Convience method for setting up a single card set for tests"""
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        oPCS = PhysicalCardSet(name=self.aNames[0])
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition')]
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
        return oPCS

    def test_adding_cards(self):
        """Test adding & removing cards from the model for the different
           groupings"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        # Test adding more cards
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        self._loop_modes(oPCS, [oModel])
        self._cleanup_models([oModel])

    def test_groupings(self):
        """Check over all the groupings, single card set"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for cGrouping in [Groupings.CryptLibraryGrouping,
                Groupings.DisciplineGrouping, Groupings.ClanGrouping,
                Groupings.CardTypeGrouping, Groupings.ExpansionGrouping,
                Groupings.RarityGrouping]:
            oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
            oModel.groupby = cGrouping
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def test_adding_filter(self):
        """Check adding cards with filters enabled"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for oFilter in [Filters.CardTypeFilter('Vampire'),
                Filters.PhysicalExpansionFilter('Sabbat'),
                Filters.CardSetMultiCardCountFilter((['2','3'],
                    self.aNames[0])),
                ]:
            oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
            oModel.groupby = Groupings.NullGrouping
            oModel.selectfilter = oFilter
            oModel.applyfilter = True
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def test_relationships(self):
        """Tests Model against more complex Card Set relationships"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # Add cards
        aCards = [(u'Agent of Power', None), ('Alexandra', 'CE'),
                ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        aModels = []
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
        # Create a child card set with some entries and check everything works
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        for sName, sExp in aCards[2:6] + [(u'Two Wrongs', None)]:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChildPCS.addPhysicalCard(oCard.id)
        oChildPCS.inuse = False
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oChildModel = CardSetCardListModel(self.aNames[1], self.oConfig)
        oModel.groupby = Groupings.NullGrouping
        oChildModel.groupby = Groupings.NullGrouping
        aModels = [oModel, oChildModel]
        self._loop_modes(oPCS, aModels)
        self._loop_modes(oChildPCS, aModels)
        # And when we're in use
        oChildPCS.inuse = True
        self._loop_modes(oChildPCS, aModels)
        self._loop_modes(oPCS, aModels)
        # Add a grand child
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        for sName, sExp in aCards[3:7]:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oGrandChildPCS.addPhysicalCard(oCard.id)
        oGrandChildModel = CardSetCardListModel(self.aNames[2], self.oConfig)
        oGrandChildModel.groupby = Groupings.NullGrouping
        aModels.append(oGrandChildModel)
        oGrandChildPCS.inuse = False
        # Check adding cards when we have a parent card set and a child
        self._loop_modes(oChildPCS, aModels)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, aModels)
        # Add some cards to oGrandChildPCS that aren't in parent and oChildPCS,
        # add a sibling card set to oChildPCS and add another child and retest
        oSibPCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS)
        for sName, sExp in aCards[1:6]:
            oCard = make_card(sName, sExp)
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
            oCard = make_card(sName, sExp)
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
        self._loop_modes(oChildPCS, aModels)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, aModels)
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        oGrandChild2PCS.addPhysicalCard(make_card('Ablative Skin',
            'Sabbat'))
        self._loop_modes(oChildPCS, aModels)
        oChildPCS.addPhysicalCard(make_card('Ablative Skin',
            'Sabbat'))
        oGrandChild2PCS.addPhysicalCard(make_card(
            'Ablative Skin', None))
        self._loop_modes(oSibPCS, aModels)
        self._loop_modes(oGrandChild2PCS, aModels)
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def _setup_relationships(self):
        """Convience method to setup a card set hierachy for test cases"""
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # Add cards
        aCards = [(u'Agent of Power', None), ('Alexandra', 'CE'),
                ('Alexandra', 'CE'), ('Alexandra', 'CE'),
                ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        for sName, sExp in aCards[2:6] + [(u'Two Wrongs', None),
                ('Ablative Skin', None)]:
            oCard = make_card(sName, sExp)
            oChildPCS.addPhysicalCard(oCard.id)
        oChildPCS.inuse = True
        oSibPCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS)
        for sName, sExp in aCards[1:6]:
            oCard = make_card(sName, sExp)
            oSibPCS.addPhysicalCard(oCard.id)
        oSibPCS.inuse = True
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2],
                parent=oChildPCS)
        oGrandChild2PCS = PhysicalCardSet(name=self.aNames[4],
                parent=oChildPCS)
        oGrandChildPCS.inuse = True
        oGrandChild2PCS.inuse = True
        for sName, sExp in aCards[3:7] + [('Aire of Elation', 'CE')] * 3:
            oCard = make_card(sName, sExp)
            oGrandChildPCS.addPhysicalCard(oCard.id)
        aGC2Cards = [('AK-47', 'LotN'), ('Cesewayo', 'LoB'),
                ('Aire of Elation', 'CE'), ('Yvette, The Hopeless', None),
                ('Yvette, The Hopeless', 'BSC'), ('Ablative Skin', 'Sabbat'),
                ('Ablative Skin', None)]
        for sName, sExp in aGC2Cards:
            oCard = make_card(sName, sExp)
            oGrandChild2PCS.addPhysicalCard(oCard.id)
            oGrandChild2PCS.syncUpdate()
        return oChildPCS

    def test_relation_grouping(self):
        """Test groupings with complex relationships"""
        # Go through some of grouping tests as well
        # We want to ensure that this works with non-NullGroupings,
        # but we don't need to cover all the groupings again
        _oCache = SutekhObjectCache()
        oChildPCS = self._setup_relationships()
        aModels = []
        for cGrouping in [Groupings.DisciplineGrouping,
                Groupings.CardTypeGrouping]:
            for sName in self.aNames[:4]:
                oModel = CardSetCardListModel(sName, self.oConfig)
                oModel.groupby = cGrouping
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        self._cleanup_models(aModels)

    def test_relation_filters(self):
        """Test adding with complex relationships and filters"""
        _oCache = SutekhObjectCache()
        oChildPCS = self._setup_relationships()
        aModels = []
        for oFilter in [
                Filters.CardTypeFilter('Vampire'),
                Filters.PhysicalExpansionFilter('Sabbat'),
                Filters.CardSetMultiCardCountFilter((['2','3'],
                    self.aNames[0])),
                ]:
            for sName in self.aNames[:4]:
                oModel = CardSetCardListModel(sName, self.oConfig)
                oModel.selectfilter = oFilter
                oModel.groupby = Groupings.NullGrouping
                oModel.applyfilter = True
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        self._cleanup_models(aModels)

    def test_filters(self):
        """Test filtering for the card set"""
        # pylint: disable-msg=R0915
        # R0915: Want a long, sequential test case to reduce
        # repeated setups, so it has lots of lines
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
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
            oCard = make_card(sName, sExp)
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
        tExpected = (1, 30, 4)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))

    def test_empty(self):
        """Test corner cases around empty card sets"""
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        oGrandChildPCS.inuse = True
        oChildModel = CardSetCardListModel(self.aNames[1], self.oConfig)
        oChildModel.groupby = Groupings.NullGrouping
        self._loop_modes(oChildPCS, [oChildModel])
        self._loop_modes(oPCS, [oChildModel])
        self._loop_modes(oGrandChildPCS, [oChildModel])
        # Add some cards to parent + child card sets
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
            if sName != 'Yvette, The Hopeless':
                oGrandChildPCS.addPhysicalCard(oCard.id)
        self._loop_modes(oChildPCS, [oChildModel])

if __name__ == "__main__":
    unittest.main()
