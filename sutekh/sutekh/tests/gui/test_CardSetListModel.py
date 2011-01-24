# test_CardSetListModel.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable-msg=C0302
# This tests the card set list model extensively, so it's quite long

"""Tests the Card List Model"""

from sutekh.tests.GuiSutekhTest import ConfigSutekhTest
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.gui.ConfigFile import CARDSET, FRAME
from sutekh.gui.CardSetListModel import CardSetCardListModel, \
        EXTRA_LEVEL_OPTION, EXTRA_LEVEL_LOOKUP, SHOW_CARD_OPTION, \
        SHOW_CARD_LOOKUP, PARENT_COUNT_MODE, PARENT_COUNT_LOOKUP, \
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


class DummyController(object):
    """Dummy controller object for config tests"""

    def __init__(self):
        self.bReload = False

    # pylint: disable-msg=W0212
    # We allow access via these properties

    view = property(fget=lambda self: self)
    frame = property(fget=lambda self: self)
    pane_id = property(fget=lambda self: 10)
    config_frame_id = property(fget=lambda self: 'pane10')

    # pylint: enable-msg=W0212

    # pylint: disable-msg=R0201, C0111
    # dummy functions, so they're empty

    def set_parent_count_col_vis(self, _bVal):
        return

    def reload_keep_expanded(self):
        return

    def queue_reload(self):
        self.bReload = True  # For use in listener test cases


class CardSetListModelTests(ConfigSutekhTest):
    """Class for the test cases"""
    # pylint: disable-msg=R0904
    # R0904: We test a number of sepetate bits, so many methods

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
        # We use get_value rather than get_name_from_iter, as we're
        # not worried about the encoding issues here, and it saves time.
        aList = []
        oChildIter = oModel.iter_children(oIter)
        while oChildIter:
            if sName:
                sListName = sName + ':' + oModel.get_value(oChildIter, 0)
            else:
                sListName = oModel.get_value(oChildIter, 0)
            # similiarly, we use get_value rather than the count functions
            # for speed as well
            aList.append((oModel.get_value(oChildIter, 1),
                oModel.get_value(oChildIter, 2), sListName))
            if oModel.iter_n_children(oChildIter) > 0:
                oGCIter = oModel.iter_children(oChildIter)
                # We unroll a level for speed reasons
                # This is messy - we could easily do this as a recursive call
                # in all cases, but we hit this function 4 times for almost
                # every iteration of the test, so sacrificing some readablity
                # for speed is worthwhile
                while oGCIter:
                    sGCName = sListName + ':' + \
                            oModel.get_value(oGCIter, 0)
                    if oModel.iter_n_children(oGCIter) > 0:
                        aList.extend(self._get_all_child_counts(oModel,
                            oGCIter, sGCName))
                    else:
                        aList.append((oModel.get_value(oGCIter, 1),
                            oModel.get_value(oGCIter, 2), sGCName))
                    oGCIter = oModel.iter_next(oGCIter)
            oChildIter = oModel.iter_next(oChildIter)
        return aList

    def _get_all_counts(self, oModel):
        """Return a list of iCnt, iParCnt, sCardName tuples from the Model"""
        return sorted(self._get_all_child_counts(oModel, None))

    def _check_cache_totals(self, oCS, oModelCache, oModelNoCache, sMode):
        """Reload the models and check the totals match"""
        oModelNoCache._dCache = {}
        oModelCache.load()
        oModelNoCache.load()
        tCacheTotals = (
                oModelCache.iter_n_children(None),
                self._count_all_cards(oModelCache),
                self._count_second_level(oModelCache))
        aCacheList = self._get_all_counts(oModelCache)
        tNoCacheTotals = (
                oModelNoCache.iter_n_children(None),
                self._count_all_cards(oModelNoCache),
                self._count_second_level(oModelNoCache))
        aNoCacheList = self._get_all_counts(oModelNoCache)
        self.assertEqual(tCacheTotals, tNoCacheTotals,
                self._format_error("Totals for cache and no-cache differ "
                    "after %s cards" % sMode, tCacheTotals, tNoCacheTotals,
                    oModelCache, oCS))
        self.assertEqual(aCacheList, aNoCacheList,
                self._format_error("Card Lists for cache and no-cache "
                    "differ after %s cards" % sMode, aCacheList,
                    aNoCacheList, oModelCache, oCS))

    def _reset_modes(self, oModel):
        """Set the model to the minimal state."""
        # pylint: disable-msg=W0212
        # we need to access protected methods
        # The database signal handling means that all CardSetListModels
        # associated with a card set will update when send_changed_signal is
        # called, so we reset the model state so these calls will be cheap if
        # this models is affected when we're not explicitly testing it.
        oModel._change_parent_count_mode(IGNORE_PARENT)
        oModel._change_level_mode(NO_SECOND_LEVEL)
        oModel.bEditable = False
        oModel._change_count_mode(THIS_SET_ONLY)

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
                        self.aExtraLevelToStr[oModel._iExtraLevelsMode],
                        self.aParentCountToStr[oModel._iParentCountMode],
                        self.aCardCountToStr[oModel._iShowCardMode],
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

    def _add_remove_cards(self, oPCS, aModels, dCountInfo):
        """Helper function to add and remove distinct cards from the card set,
           validating that the model works correctly"""
        # pylint: disable-msg=E1101, R0914
        # E1101: SQLObjext confuses pylint
        # R0914: several local variables, as we test a number of conditions
        dModelInfo = {}
        for oModel in aModels:
            oListener = CardSetListener()
            oModel.add_listener(oListener)
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
            if not dCountInfo[oModel]['added']:
                iSetCnt = oModel.get_card_iterator(
                        oModel.get_current_filter()).count()
                dCountInfo[oModel]['added'] = iSetCnt
            else:
                iSetCnt = dCountInfo[oModel]['added']
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
            iSetCnt = dCountInfo[oModel]['start']
            self.assertEqual(oListener.iCnt, iSetCnt, self._format_error(
                "Listener has wrong count after dec_card", oListener.iCnt,
                iSetCnt, oModel, oPCS))
            oModel.remove_listener(oListener)

    def _loop_modes(self, oPCS, aModels):
        """Loop over all the possible modes of the model, calling
           _add_remove_cards to test the model."""
        # pylint: disable-msg=W0212
        # we need to access protected methods
        dCountInfo = {}
        for oModel in aModels:
            # We cache these lookups, since the various modes don't change
            # these numbers
            dCountInfo[oModel] = {}
            iSetCnt = oModel.get_card_iterator(
                    oModel.get_current_filter()).count()
            dCountInfo[oModel]['start'] = iSetCnt
            dCountInfo[oModel]['added'] = None
            # Ensure we start with a clean cache
            oModel._dCache = {}
        for bEditFlag in (False, True):
            for oModel in aModels:
                oModel.bEditable = bEditFlag
            for iShowMode in (ALL_CARDS, PARENT_CARDS, CHILD_CARDS,
                    THIS_SET_ONLY):
                for oModel in aModels:
                    oModel._change_count_mode(iShowMode)
                for iLevelMode in (NO_SECOND_LEVEL, SHOW_EXPANSIONS,
                        SHOW_CARD_SETS, EXP_AND_CARD_SETS, CARD_SETS_AND_EXP):
                    for oModel in aModels:
                        oModel._change_level_mode(iLevelMode)
                    for iParentMode in (PARENT_COUNT, MINUS_THIS_SET,
                            MINUS_SETS_IN_USE, IGNORE_PARENT):
                        for oModel in aModels:
                            oModel._change_parent_count_mode(iParentMode)
                        self._add_remove_cards(oPCS, aModels, dCountInfo)
        for oModel in aModels:
            self._reset_modes(oModel)

    def _loop_zero_filter_modes(self, oModel):
        """Loop over all the possible modes of the model, calling
           a zero result filters to test the model."""
        # pylint: disable-msg=W0212
        # we need to access protected methods
        for bEditFlag in (False, True):
            oModel.bEditable = bEditFlag
            for iLevelMode in (NO_SECOND_LEVEL, SHOW_EXPANSIONS,
                    SHOW_CARD_SETS, EXP_AND_CARD_SETS, CARD_SETS_AND_EXP):
                oModel._change_level_mode(iLevelMode)
                for iParentMode in (IGNORE_PARENT, PARENT_COUNT,
                        MINUS_THIS_SET, MINUS_SETS_IN_USE):
                    oModel._change_parent_count_mode(iParentMode)
                    for iShowMode in (THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS,
                            CHILD_CARDS):
                        oModel._change_count_mode(iShowMode)
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
                {'Camarilla Edition': 1})
        self.assertEqual(oModel.get_drag_info_from_path('0:0:0'),
                (u"Alexandra", "Camarilla Edition", 1, 2))
        self.assertEqual(oModel.get_drag_info_from_path('0:0'),
                (u"Alexandra", None, 1, 1))
        self.assertEqual(oModel.get_drag_info_from_path('0'),
                (None, None, 2, 0))
        # pylint: disable-msg=W0212
        # we need to access this protected methods
        oModel._change_level_mode(NO_SECOND_LEVEL)
        oModel.load()
        # This should also work for no expansions shown
        self.assertEqual(self._count_all_cards(oModel), 2)
        self.assertEqual(self._count_second_level(oModel), 0)
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                {'Camarilla Edition': 1})
        self._cleanup_models([oModel])

    def test_db_listeners(self):
        """Test that the model responds to changes to the card set hierarchy"""
        # We use an empty card set for these tests, to minimise time taken
        # pylint: disable-msg=W0212
        # we need to access protected methods
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oDummy = DummyController()
        oModel.set_controller(oDummy)
        oPCS2 = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        # Child tests
        self.assertEqual(oDummy.bReload, False)
        oPCS2.inuse = True
        self.assertEqual(oDummy.bReload, False)
        oModel._change_count_mode(CHILD_CARDS)
        oPCS2.inuse = False
        self.assertEqual(oDummy.bReload, True)
        oDummy.bReload = False
        PhysicalCardSet.delete(oPCS2.id)
        self.assertEqual(oDummy.bReload, False)
        oPCS2 = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        self.assertEqual(oDummy.bReload, False)
        oPCS2.inuse = True
        self.assertEqual(oDummy.bReload, True)
        oDummy.bReload = False
        PhysicalCardSet.delete(oPCS2.id)
        self.assertEqual(oDummy.bReload, True)
        oPCS2 = PhysicalCardSet(name=self.aNames[1])
        oPCS.parent = oPCS2
        oPCS3 = PhysicalCardSet(name=self.aNames[2], parent=oPCS2)
        oPCS3.inuse = True
        oModel._change_count_mode(PARENT_CARDS)
        oModel._change_parent_count_mode(MINUS_SETS_IN_USE)
        oDummy.bReload = False
        oPCS3.inuse = False
        self.assertEqual(oDummy.bReload, True)
        oDummy.bReload = False
        oPCS.parent = None
        self.assertEqual(oDummy.bReload, True)
        oDummy.bReload = False
        oPCS3.inuse = True
        self.assertEqual(oDummy.bReload, False)
        self._cleanup_models([oModel])

    def test_config_listener(self):
        """Test that the model responds to the profile changes as expected"""
        # We use an empty card set for these tests, to minimise time taken
        # pylint: disable-msg=W0212
        # we need to access protected methods
        PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oDummy = DummyController()
        oModel.set_controller(oDummy)
        sTestValue = list(SHOW_CARD_LOOKUP)[0]
        iTestMode = SHOW_CARD_LOOKUP[sTestValue]
        self.oConfig.set_profile_option(CARDSET, 'test', SHOW_CARD_OPTION,
                sTestValue)
        self.oConfig.set_profile_option(CARDSET, 'test2', SHOW_CARD_OPTION,
                sTestValue)
        # Check changing deck profile
        for sValue, iMode in SHOW_CARD_LOOKUP.iteritems():
            iCurMode = oModel._iShowCardMode
            self.oConfig.set_profile_option(CARDSET, 'test', SHOW_CARD_OPTION,
                    sValue)
            self.assertEqual(oModel._iShowCardMode, iCurMode)
            self.oConfig.set_profile(CARDSET, oModel.cardset_id, 'test')
            self.assertEqual(oModel._iShowCardMode, iMode)
            self.oConfig.set_profile(FRAME, oModel.frame_id, 'test2')
            self.assertEqual(oModel._iShowCardMode, iTestMode)
            self.oConfig.set_profile(FRAME, oModel.frame_id, 'defaults')
            self.oConfig.set_profile(CARDSET, oModel.cardset_id, 'defaults')
        # Check listener on card set profile changes
        self.oConfig.set_profile(CARDSET, oModel.cardset_id, 'test')
        self.oConfig.set_profile(FRAME, oModel.frame_id, 'test2')
        for sValue, iMode in EXTRA_LEVEL_LOOKUP.iteritems():
            self.oConfig.set_profile_option(CARDSET, 'test',
                    EXTRA_LEVEL_OPTION, sValue)
            self.assertEqual(oModel._iExtraLevelsMode, iMode)
        # Check listener on frame profile changes
        for sValue, iMode in PARENT_COUNT_LOOKUP.iteritems():
            self.oConfig.set_profile_option(CARDSET, 'test2',
                    PARENT_COUNT_MODE, sValue)
            self.assertEqual(oModel._iParentCountMode, iMode)
        # Check listener on local frame profile changes
        for sValue, iMode in PARENT_COUNT_LOOKUP.iteritems():
            self.oConfig.set_local_frame_option(oModel.frame_id,
                    PARENT_COUNT_MODE, sValue)
            self.assertEqual(oModel._iParentCountMode, iMode)
        self._cleanup_models([oModel])

    def _get_model(self, sName):
        """Return a model for the named card set, with the null grouping"""
        oModel = CardSetCardListModel(sName, self.oConfig)
        oModel.hideillegal = False
        oModel.groupby = Groupings.NullGrouping
        return oModel

    def _setup_simple(self):
        """Convenience method for setting up a single card set for tests"""
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
        """Test adding & removing cards from the model"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        # Test adding more cards
        oModel = self._get_model(self.aNames[0])
        self._loop_modes(oPCS, [oModel])
        oModel.hideillegal = True
        self._loop_modes(oPCS, [oModel])
        self._cleanup_models([oModel])

    def test_groupings(self):
        """Check over various groupings, single card set"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for cGrouping in (Groupings.CryptLibraryGrouping,
                Groupings.DisciplineGrouping, Groupings.ClanGrouping,
                Groupings.CardTypeGrouping, Groupings.ExpansionGrouping,
                Groupings.RarityGrouping):
            oModel = self._get_model(self.aNames[0])
            oModel.groupby = cGrouping
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def test_adding_filter(self):
        """Check adding cards with filters enabled (single card set)"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for oFilter in (Filters.CardTypeFilter('Vampire'),
                Filters.PhysicalExpansionFilter('Sabbat'),
                Filters.CardSetMultiCardCountFilter((['2', '3'],
                    self.aNames[0])),
                ):
            oModel = self._get_model(self.aNames[0])
            oModel.selectfilter = oFilter
            oModel.applyfilter = True
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def test_cache_simple(self):
        """Test that the special persistent caches don't affect results"""
        # pylint: disable-msg=W0212
        # we need to access protected methods
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        oModelCache = self._get_model(self.aNames[0])
        oModelNoCache = self._get_model(self.aNames[0])
        aModels = [oModelCache, oModelNoCache]
        # We need to catch some corner cases around adding only 1 copy before
        # reloading as well
        aCardsToAdd = self.aPhysCards[1:8:2] + self.aPhysCards[9:]
        # We test a much smaller range of things than in loop_modes
        for bEditFlag in (False, True):
            for oModel in aModels:
                oModel.bEditable = bEditFlag
            for iLevelMode in (NO_SECOND_LEVEL, SHOW_EXPANSIONS):
                for oModel in aModels:
                    oModel._change_level_mode(iLevelMode)
                for iShowMode in (THIS_SET_ONLY, ALL_CARDS):
                    for oModel in aModels:
                        oModel._change_count_mode(iShowMode)
                        oModel.load()
                    # pylint: disable-msg=E1101
                    # E1101: SQLObjext confuses pylint
                    for oCard in aCardsToAdd:
                        oPCS.addPhysicalCard(oCard.id)
                        oPCS.syncUpdate()
                        send_changed_signal(oPCS, oCard, 1)
                    self._check_cache_totals(oPCS, oModelCache, oModelNoCache,
                            'adding')
                    for oCard in aCardsToAdd:
                        oMapEntry = list(
                                MapPhysicalCardToPhysicalCardSet.selectBy(
                                    physicalCardID=oCard.id,
                                    physicalCardSetID=oPCS.id))[-1]
                        MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
                        oPCS.syncUpdate()
                        send_changed_signal(oPCS, oCard, -1)
                    self._check_cache_totals(oPCS, oModelCache, oModelNoCache,
                            'deleting')

        self._cleanup_models(aModels)

    def test_cache_complex(self):
        """Test that the special persistent caches don't affect results with
           more complex card set relationships"""
        # pylint: disable-msg=W0212, R0914
        # we need to access protected methods
        # We loop over a lot of combinations, so lots of local variables
        _oCache = SutekhObjectCache()
        aNoCache = []
        aCache = []
        aCards, oPCS, oChildPCS = self._setup_parent_child()
        oGrandChildPCS = self._setup_grand_child(aCards, oChildPCS)
        oChildPCS.inuse = True
        oGrandChildPCS.inuse = True
        oChildPCS.syncUpdate()
        oGrandChildPCS.syncUpdate()
        oEmptyPCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS)
        oEmptyPCS.inuse = True
        oEmptyPCS.syncUpdate()
        for sName in self.aNames[:4]:
            oModelCache = self._get_model(sName)
            oModelCache._change_parent_count_mode(MINUS_SETS_IN_USE)
            aCache.append(oModelCache)
            oModelNoCache = self._get_model(sName)
            oModelNoCache._change_parent_count_mode(MINUS_SETS_IN_USE)
            aNoCache.append(oModelNoCache)
        aModels = aCache + aNoCache
        # See test_cache_simple
        aCardsToAdd = self.aPhysCards[1:8:2] + self.aPhysCards[9:]
        # We test a much smaller range of things than in loop_modes
        for bEditFlag in (False, True):
            for oModel in aModels:
                oModel.bEditable = bEditFlag
            for iLevelMode in (NO_SECOND_LEVEL, SHOW_EXPANSIONS):
                for oModel in aModels:
                    oModel._change_level_mode(iLevelMode)
                for iShowMode in (THIS_SET_ONLY, ALL_CARDS,
                        PARENT_CARDS, CHILD_CARDS):
                    for oModel in aModels:
                        oModel._change_count_mode(iShowMode)
                        oModel.load()
                    # pylint: disable-msg=E1101, E1103
                    # E1101: SQLObjext confuses pylint
                    for oCS in (oEmptyPCS, oChildPCS, oGrandChildPCS, oPCS):
                        for oCard in aCardsToAdd:
                            oCS.addPhysicalCard(oCard.id)
                            oCS.syncUpdate()
                            send_changed_signal(oCS, oCard, 1)
                        for oModelCache, oModelNoCache in \
                                zip(aCache, aNoCache):
                            self._check_cache_totals(oCS, oModelCache,
                                    oModelNoCache, 'adding')
                        for oCard in aCardsToAdd:
                            oMapEntry = list(
                                    MapPhysicalCardToPhysicalCardSet.selectBy(
                                        physicalCardID=oCard.id,
                                        physicalCardSetID=oCS.id))[-1]
                            MapPhysicalCardToPhysicalCardSet.delete(
                                    oMapEntry.id)
                            oCS.syncUpdate()
                            send_changed_signal(oCS, oCard, -1)
                        for oModelCache, oModelNoCache in \
                                zip(aCache, aNoCache):
                            self._check_cache_totals(oCS, oModelCache,
                                    oModelNoCache, 'deleting')

        self._cleanup_models(aModels)

    def _setup_parent_child(self):
        """Setup the initial parent and child for relationship tests"""
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # Add cards
        aCards = [(u'Agent of Power', None), ('Alexandra', 'CE'),
                ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
                ('Alexandra', None), ('Bronwen', 'Sabbat'),
                ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
                ('Yvette, The Hopeless', 'CE'),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oPCS.addPhysicalCard(oCard.id)
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        for sName, sExp in aCards[2:6] + [(u'Two Wrongs', None)]:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oChildPCS.addPhysicalCard(oCard.id)
        oChildPCS.inuse = False

        oChildPCS.syncUpdate()
        oPCS.syncUpdate()
        return aCards, oPCS, oChildPCS

    def _setup_grand_child(self, aCards, oChildPCS):
        """Setup the grand child for the relationship tests"""
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        for sName, sExp in aCards[3:7]:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oGrandChildPCS.addPhysicalCard(oCard.id)
        oGrandChildPCS.syncUpdate()
        return oGrandChildPCS

    def _setup_relationships(self):
        """Convenience method to setup a card set hierarchy for test cases"""
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        aCards, oPCS, oChildPCS = self._setup_parent_child()
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
        oChildPCS.syncUpdate()
        oSibPCS.syncUpdate()
        oGrandChildPCS.syncUpdate()
        oGrandChild2PCS.syncUpdate()
        return oPCS, oSibPCS, oChildPCS, oGrandChildPCS, oGrandChild2PCS

    def test_child_parent(self):
        """Tests Model against parent-child relationships"""
        _oCache = SutekhObjectCache()
        _aCards, oPCS, oChildPCS = self._setup_parent_child()
        oModel = self._get_model(self.aNames[0])
        oChildModel = self._get_model(self.aNames[1])
        aModels = [oModel, oChildModel]
        # Create a child card set with some entries and check everything works
        self._loop_modes(oPCS, aModels)
        self._loop_modes(oChildPCS, aModels)
        # And when we're in use
        oChildPCS.inuse = True
        self._loop_modes(oChildPCS, aModels)
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def test_parent_child_grandchild(self):
        """Test against parent-child-grandchild setup"""
        _oCache = SutekhObjectCache()
        aModels = []
        aCards, _oPCS, oChildPCS = self._setup_parent_child()
        oModel = self._get_model(self.aNames[0])
        oChildModel = self._get_model(self.aNames[1])
        aModels = [oModel, oChildModel]
        # Add a grand child
        oGrandChildPCS = self._setup_grand_child(aCards, oChildPCS)
        oGrandChildModel = self._get_model(self.aNames[2])
        aModels.append(oGrandChildModel)
        oGrandChildPCS.inuse = False
        # Check adding cards when we have a parent card set and a child
        self._loop_modes(oChildPCS, aModels)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, aModels)
        self._cleanup_models(aModels)

    def test_complex_heirachy(self):
        """Test with siblings in the tree as well"""
        # Add some cards to oGrandChildPCS that aren't in parent and oChildPCS,
        # add a sibling card set to oChildPCS and add another child and retest
        _oCache = SutekhObjectCache()
        aModels = []
        aCards, oPCS, oChildPCS = self._setup_parent_child()
        oModel = self._get_model(self.aNames[0])
        oChildModel = self._get_model(self.aNames[1])
        aModels = [oModel, oChildModel]
        # Add a grand child
        oGrandChildPCS = self._setup_grand_child(aCards, oChildPCS)
        # add sibling
        oSibPCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS)
        for sName, sExp in aCards[1:6]:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101
            # PyProtocols confuses pylint
            oSibPCS.addPhysicalCard(oCard.id)
        oGrandChild2PCS = PhysicalCardSet(name=self.aNames[4],
                parent=oChildPCS)
        aCards = [('AK-47', 'LotN'), ('Cesewayo', 'LoB'),
                ('Aire of Elation', 'CE'), ('Yvette, The Hopeless', None),
                ('Yvette, The Hopeless', 'BSC')]
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            # pylint: disable-msg=E1101, E1103
            # PyProtocols confuses pylint
            oGrandChild2PCS.addPhysicalCard(oCard.id)
            if sName == 'Aire of Elation':
                oGrandChildPCS.addPhysicalCard(oCard.id)
                oGrandChildPCS.addPhysicalCard(oCard.id)
                oGrandChildPCS.addPhysicalCard(oCard.id)
                oGrandChildPCS.syncUpdate()
            oGrandChild2PCS.syncUpdate()
        oSibPCS.inuse = True
        oGrandChild2PCS.inuse = True
        oGrandChildPCS.inuse = False
        # Add model
        oGrandChildModel = self._get_model(self.aNames[2])
        aModels.append(oGrandChildModel)
        self._loop_modes(oChildPCS, aModels)
        oGrandChildPCS.inuse = True
        self._loop_modes(oChildPCS, aModels)
        self._cleanup_models(aModels)

    def test_final_relationship_state(self):
        """Tests with the final relationship setup"""
        # This tests a slightly different arrangment of cards between the
        # different cards sets than test_complex_heirachy. It includes a
        # few more cards where the different physical cards of the same
        # abstract cards are split across the card sets
        _oCache = SutekhObjectCache()
        oPCS, oSibPCS, _oChildPCS, _oGrandChildPCS, oGrandChild2PCS = \
                self._setup_relationships()
        oModel = self._get_model(self.aNames[0])
        oChildModel = self._get_model(self.aNames[1])
        aModels = [oModel, oChildModel]
        oGrandChildModel = self._get_model(self.aNames[2])
        aModels.append(oGrandChildModel)
        self._loop_modes(oSibPCS, aModels)
        self._loop_modes(oGrandChild2PCS, aModels)
        # Check with legal filter on as well
        for oModel in aModels:
            oModel.hideillegal = True
        self._loop_modes(oPCS, aModels)
        self._cleanup_models(aModels)

    def test_relation_grouping(self):
        """Test groupings with complex relationships"""
        # Go through some of grouping tests as well
        # We want to ensure that this works with non-NullGroupings,
        # but we don't need to cover all the groupings again
        _oCache = SutekhObjectCache()
        _oPCS, _oSPCS, oChildPCS, _oGCPCS, _oGC2PCS = \
                self._setup_relationships()
        aModels = []
        for cGrouping in (Groupings.DisciplineGrouping,
                Groupings.CardTypeGrouping):
            for sName in self.aNames[:4]:
                oModel = self._get_model(sName)
                oModel.groupby = cGrouping
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        self._cleanup_models(aModels)

    def test_relation_filters(self):
        """Test adding with complex relationships and filters"""
        _oCache = SutekhObjectCache()
        _oPCS, _oSPCS, oChildPCS, _oGCPCS, _oGC2PCS = \
                self._setup_relationships()
        aModels = []
        for oFilter in (
                Filters.CardTypeFilter('Vampire'),
                Filters.PhysicalExpansionFilter('Sabbat'),
                Filters.CardSetMultiCardCountFilter((['2', '3'],
                    self.aNames[0])),
                ):
            for sName in self.aNames[:4]:
                oModel = self._get_model(sName)
                oModel.selectfilter = oFilter
                oModel.applyfilter = True
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        self._cleanup_models(aModels)

    def test_filters(self):
        """Test filtering for the card set"""
        # pylint: disable-msg=R0915, W0212
        # R0915: Want a long, sequential test case to reduce
        # W0212: We need to access protected methods
        # repeated setups, so it has lots of lines
        # Note that these tests are with the illegal card filter enabled
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
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
        oModel = self._get_model(self.aNames[0])
        # Test filter which selects nothing works
        self._loop_zero_filter_modes(oModel)
        # Check basic filtering
        oModel._change_count_mode(THIS_SET_ONLY)
        oModel._change_parent_count_mode(IGNORE_PARENT)
        oModel._change_level_mode(NO_SECOND_LEVEL)
        oModel.bEditable = False
        oModel.hideillegal = True
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
        oModel._change_level_mode(SHOW_EXPANSIONS)
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
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        # Do this to match how gui code works - this ensures that the
        # caches are cleared properly
        oChildPCS.inuse = True
        oChildPCS.syncUpdate()
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
        oModel._change_level_mode(SHOW_CARD_SETS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 4, 2)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel._change_count_mode(CHILD_CARDS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 6, 4)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        oModel._change_count_mode(ALL_CARDS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                self._count_all_cards(oModel),
                self._count_second_level(oModel))
        tExpected = (1, 31, 4)
        self.assertEqual(tTotals, tExpected, 'Wrong results from filter : '
                '%s vs %s' % (tTotals, tExpected))
        self._cleanup_models([oModel])

    def test_empty(self):
        """Test corner cases around empty card sets"""
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        oGrandChildPCS.inuse = True
        oChildModel = self._get_model(self.aNames[1])
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
        self._cleanup_models([oChildModel])

if __name__ == "__main__":
    unittest.main()
