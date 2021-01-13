# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# pylint: disable=too-many-lines
# This tests the card set list model extensively, so it's quite long

"""Tests the Card List Model"""

import unittest

from sutekh.base.tests.TestUtils import make_card
from sutekh.base.tests.GuiTestUtils import (LocalTestListener,
                                            DummyCardSetController,
                                            get_all_counts,
                                            count_second_level,
                                            count_all_cards,
                                            reset_modes,
                                            cleanup_models)
from sutekh.base.core.DBSignals import send_changed_signal
from sutekh.base.core import BaseFilters
from sutekh.base.core.BaseGroupings import (CardTypeGrouping,
                                            ExpansionGrouping,
                                            RarityGrouping, NullGrouping)
from sutekh.base.core.BaseTables import (PhysicalCardSet,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.gui.BaseConfigFile import CARDSET, FRAME
from sutekh.base.gui.CardSetListModel import (CardSetCardListModel,
                                              ExtraLevels, ShowMode,
                                              ParentCountMode,
                                              EXTRA_LEVEL_OPTION,
                                              EXTRA_LEVEL_LOOKUP,
                                              SHOW_CARD_OPTION,
                                              SHOW_CARD_LOOKUP,
                                              PARENT_COUNT_MODE,
                                              PARENT_COUNT_LOOKUP)
# Needed to reduce speed impact of Grouping tests
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.core.Groupings import (CryptLibraryGrouping,
                                   DisciplineGrouping, ClanGrouping)
from sutekh.tests.GuiSutekhTest import ConfigSutekhTest


class CardSetListModelTests(ConfigSutekhTest):
    """Class for the test cases"""
    # pylint: disable=too-many-public-methods
    # We test a number of sepetate bits, so many methods

    aNames = ['Test 1', 'Test Child 1', 'Test Grand Child', 'Test Sibling',
              'Test Grand Child 2']

    def _check_cache_totals(self, oCS, oModelCache, oModelNoCache, sMode):
        """Reload the models and check the totals match"""
        # pylint: disable=protected-access
        # allow access to _dCache for testing here
        oModelNoCache._dCache = {}
        # pylint: enable=protected-access
        oModelCache.load()
        oModelNoCache.load()
        tCacheTotals = (
            oModelCache.iter_n_children(None),
            count_all_cards(oModelCache),
            count_second_level(oModelCache))
        # For speed, the model isn't sorted, so we need to sort the results
        # for sanity
        aCacheList = sorted(get_all_counts(oModelCache))
        tNoCacheTotals = (
            oModelNoCache.iter_n_children(None),
            count_all_cards(oModelNoCache),
            count_second_level(oModelNoCache))
        aNoCacheList = sorted(get_all_counts(oModelNoCache))
        self.assertEqual(tCacheTotals, tNoCacheTotals,
                         self._format_error(
                             "Totals for cache and no-cache differ "
                             "after %s cards" % sMode,
                             tCacheTotals, tNoCacheTotals, oModelCache, oCS))
        self.assertEqual(aCacheList, aNoCacheList,
                         self._format_error(
                             "Card Lists for cache and no-cache "
                             "differ after %s cards" % sMode,
                             aCacheList, aNoCacheList, oModelCache, oCS))

    # pylint: disable=too-many-arguments
    # Need all these arguments here
    def _format_error(self, sErrType, oTest1, oTest2, oModel, oPCS=None):
        """Format an informative error message"""
        # pylint: disable=protected-access
        # Need info from _oCardSet here
        if oPCS:
            sModel = "Changing card set %s\n" % oPCS.name
        else:
            sModel = ''
        sModel += "Model: [card set %s, inuse=%s, groupby=%s]\n" % (
            oModel._oCardSet.name, oModel._oCardSet.inuse, oModel.groupby)
        if oModel.applyfilter:
            sModel += "Filter: %s\n" % oModel.selectfilter
        if oModel.configfilter:
            sModel += "Config Filter: %s\n" % oModel.configfilter
        sModel += (" State : (ExtraLevelsMode %s, ParentCountMode : %s, "
                   "ShowCardMode : %s, Editable: %s)" % (
                       oModel._eExtraLevelsMode, oModel._eParentCountMode,
                       oModel._eShowCardMode, oModel.bEditable))
        return "%s : %s vs %s\n%s" % (sErrType, oTest1, oTest2, sModel)

    # pylint: enable=no-self-use
    # pylint: enable=too-many-arguments

    # pylint: disable=invalid-name
    # setUp + tearDown names are needed by unittest - use their convention
    def setUp(self):
        """Setup the card list used in _loop_modes"""
        super().setUp()
        aCards = [
            ('AK-47', None, None), ('Bronwen', 'SW', None),
            ('Cesewayo', None, None),
            ('Anna "Dictatrix11" Suljic', 'NoR', None),
            (u'Étienne Fauberge', "Anarchs", None),
            ('Ablative Skin', 'Sabbat', None),
            ('Hektor', 'Third', "Sketch"),
            ('Walk of Flame', 'Third Edition', None),
            ('Walk of Flame', 'Third Edition', "No Draft Text"),
        ] + [
            ('Alexandra', 'CE', None), ('Alexandra', None, None),
            ('Ablative Skin', None, None), (u'Two Wrongs', None, None),
            (u'Agent of Power', None, None),
            ("Walk of Flame", "Jyhad", "Variant Printing"),
        ] * 2
        self.aPhysCards = []
        for sName, sExp, sPrint in aCards:
            oCard = make_card(sName, sExp, sPrint)
            self.aPhysCards.append(oCard)

    # pylint: enable=invalid-name

    def _add_remove_cards(self, oPCS, aModels, dCountInfo):
        """Helper function to add and remove distinct cards from the card set,
           validating that the model works correctly"""
        # pylint: disable=too-many-locals
        # several local variables, as we test a number of conditions
        # For speed, the model isn't sorted, so we need to sort the results
        # for sanity
        dModelInfo = {}
        for oModel in aModels:
            oListener = LocalTestListener(oModel, False)
            oModel.load()
            tStartTotals = (
                oModel.iter_n_children(None),
                count_all_cards(oModel),
                count_second_level(oModel))
            aStartList = sorted(get_all_counts(oModel))
            dModelInfo[oModel] = [oListener, tStartTotals, aStartList]
        for oCard in self.aPhysCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, 1)
        for oModel in aModels:
            tAddTotals = (
                oModel.iter_n_children(None),
                count_all_cards(oModel),
                count_second_level(oModel))
            aAddList = sorted(get_all_counts(oModel))
            oModel.load()
            tLoadTotals = (
                oModel.iter_n_children(None),
                count_all_cards(oModel),
                count_second_level(oModel))
            aLoadList = sorted(get_all_counts(oModel))
            self.assertEqual(tAddTotals, tLoadTotals,
                             self._format_error(
                                 "Totals for inc_card and load differ",
                                 tAddTotals, tLoadTotals, oModel, oPCS))
            self.assertEqual(aAddList, aLoadList,
                             self._format_error(
                                 "Card Lists for inc_card and load differ",
                                 aAddList, aLoadList, oModel, oPCS))
            if not dCountInfo[oModel]['added']:
                iSetCnt = oModel.get_card_iterator(
                    oModel.get_current_filter()).count()
                dCountInfo[oModel]['added'] = iSetCnt
            else:
                iSetCnt = dCountInfo[oModel]['added']
            iListCnt = dModelInfo[oModel][0].iCnt
            self.assertEqual(iListCnt, iSetCnt,
                             self._format_error(
                                 "Listener has wrong count after inc_card",
                                 iListCnt, iSetCnt, oModel, oPCS))
        # Card removal
        # We use the map table, so we can also test dec_card properly
        for oCard in self.aPhysCards:
            oMapEntry = list(
                MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, physicalCardSetID=oPCS.id))[-1]
            MapPhysicalCardToPhysicalCardSet.delete(oMapEntry.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, -1)
        for oModel in aModels:
            tDecTotals = (
                oModel.iter_n_children(None),
                count_all_cards(oModel),
                count_second_level(oModel))
            aDecList = sorted(get_all_counts(oModel))
            # test that we've behaved sanely
            oListener, tStartTotals, aStartList = dModelInfo[oModel]
            self.assertEqual(aDecList, aStartList,
                             self._format_error(
                                 "Card lists for dec_card and load differ",
                                 aDecList, aStartList, oModel, oPCS))
            self.assertEqual(tDecTotals, tStartTotals,
                             self._format_error(
                                 "Totals for dec_card and load differ",
                                 tDecTotals, tStartTotals, oModel, oPCS))
            iSetCnt = dCountInfo[oModel]['start']
            self.assertEqual(oListener.iCnt, iSetCnt,
                             self._format_error(
                                 "Listener has wrong count after dec_card",
                                 oListener.iCnt, iSetCnt, oModel, oPCS))

    def _loop_modes(self, oPCS, aModels):
        """Loop over all the possible modes of the model, calling
           _add_remove_cards to test the model."""
        # pylint: disable=protected-access
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
            for iShowMode in ShowMode:
                for oModel in aModels:
                    oModel._change_count_mode(iShowMode)
                for iLevelMode in ExtraLevels:
                    for oModel in aModels:
                        oModel._change_level_mode(iLevelMode)
                    for eParentMode in ParentCountMode:
                        for oModel in aModels:
                            oModel._change_parent_count_mode(eParentMode)
                        self._add_remove_cards(oPCS, aModels, dCountInfo)
        for oModel in aModels:
            reset_modes(oModel)

    def _loop_modes_reparent(self, oPCS, oChildPCS, aModels):
        """Loop over all the possible modes of the models,
           reparenting the oChildPCS inbetween."""
        # pylint: disable=protected-access
        # We need to access protected methods
        # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-locals
        # We need all these blocks to cover all the cases
        # covering all the cases requires a lot of branches and local vars
        for oModel in aModels:
            # Ensure we start with a clean cache
            oController = DummyCardSetController()
            oModel.set_controller(oController)
            oModel._dCache = {}
        for bEditFlag in (False, True):
            for oModel in aModels:
                oModel.bEditable = bEditFlag
            for iShowMode in ShowMode:
                for oModel in aModels:
                    oModel._change_count_mode(iShowMode)
                for iLevelMode in ExtraLevels:
                    for oModel in aModels:
                        oModel._change_level_mode(iLevelMode)
                    for eParentMode in ParentCountMode:
                        for oModel in aModels:
                            oModel._change_parent_count_mode(eParentMode)
                        for oModel in aModels:
                            oModel.load()
                        # reparent
                        oOldParPCS = oChildPCS.parent
                        oChildPCS.parent = oPCS
                        oChildPCS.syncUpdate()
                        # Handle any queued reloads
                        # This is to mimic the way we use Gtk event queuing
                        # to ensure reloads happen after database changes
                        # have been committed
                        for oModel in aModels:
                            if oModel._oController.bReload:
                                oModel.load()
                                oModel._oController.bReload = False
                        # get post-reparent counts
                        dModelInfo = {}
                        for oModel in aModels:
                            tStartTotals = (
                                oModel.iter_n_children(None),
                                count_all_cards(oModel),
                                count_second_level(oModel))
                            aStartList = sorted(get_all_counts(oModel))
                            dModelInfo[oModel] = [tStartTotals, aStartList]
                        # get post-reload counts
                        for oModel in aModels:
                            oModel.load()
                            tLoadTotals = (
                                oModel.iter_n_children(None),
                                count_all_cards(oModel),
                                count_second_level(oModel))
                            aLoadList = sorted(get_all_counts(oModel))
                            tStartTotals, aStartList = dModelInfo[oModel]
                            self.assertEqual(
                                aLoadList, aStartList,
                                self._format_error(
                                    "Card lists for reparent and load differ",
                                    aStartList, aLoadList, oModel,
                                    oChildPCS))
                            self.assertEqual(
                                tLoadTotals, tStartTotals,
                                self._format_error(
                                    "Totals for reparent and load differ",
                                    tStartTotals, tLoadTotals, oModel,
                                    oChildPCS))
                        # reset parent
                        oChildPCS.parent = oOldParPCS
                        oChildPCS.syncUpdate()
        for oModel in aModels:
            reset_modes(oModel)

    def _loop_zero_filter_modes(self, oModel):
        """Loop over all the possible modes of the model, calling
           a zero result filters to test the model."""
        # pylint: disable=protected-access
        # we need to access protected methods
        for bEditFlag in (False, True):
            oModel.bEditable = bEditFlag
            for iLevelMode in ExtraLevels:
                oModel._change_level_mode(iLevelMode)
                for eParentMode in ParentCountMode:
                    oModel._change_parent_count_mode(eParentMode)
                    for iShowMode in ShowMode:
                        oModel._change_count_mode(iShowMode)
                        oModel.selectfilter = BaseFilters.CardNameFilter(
                            'ZZZZZZZ')
                        oModel.applyfilter = True
                        oModel.load()
                        tFilterTotals = (
                            oModel.iter_n_children(None),
                            count_all_cards(oModel),
                            count_second_level(oModel))
                        self.assertEqual(
                            tFilterTotals, (1, 0, 0),
                            self._format_error(
                                "Totals for filter differ"
                                " from expected zero result",
                                tFilterTotals, (1, 0, 0), oModel))

    def test_basic(self):
        """Set of simple tests of the Card Set List Model"""
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oListener = LocalTestListener(oModel, False)
        self.assertFalse(oListener.bLoadCalled)
        oModel.load()
        self.assertTrue(oListener.bLoadCalled)
        self.assertEqual(oListener.iCnt, 0)
        # Check for the 'No cards' entry in the model
        self.assertEqual(oModel.iter_n_children(None), 1)
        aCards = [('Alexandra', 'CE', None),
                  ('Sha-Ennu', 'Third Edition', None),
                  (u'Étienne Fauberge', "Anarchs", None),
                  ("Hektor", "Third", "Sketch")]
        for sName, sExp, sPrint in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp, sPrint)
            oPCS.addPhysicalCard(oCard.id)
        oAlex = make_card('Alexandra', 'CE')
        # Test variant is added as the correct card
        oHektor = make_card('Hektor', "Third", "Sketch")
        # So we also test with unicode card names
        oEtienne = make_card(u'Étienne Fauberge', "Anarchs")
        oModel.load()
        self.assertEqual(oListener.iCnt, 4)
        # Only Vampires added
        self.assertEqual(oModel.iter_n_children(None), 1)
        oModel.groupby = NullGrouping
        self.assertEqual(count_all_cards(oModel), 4)
        self.assertEqual(count_second_level(oModel), 4)
        # These tests need the model to be sorted
        oModel.enable_sorting()
        # Check the drag-n-drop helper
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0:0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                         {oAlex.id: 1})
        self.assertEqual(oModel.get_drag_child_info('0:1'),
                         {oHektor.id: 1})
        # Étienne sorts to the end of the list
        self.assertEqual(oModel.get_drag_child_info('0:3'),
                         {oEtienne.id: 1})
        self.assertEqual(oModel.get_drag_info_from_path('0:0:0'),
                         (oAlex.abstractCard.id, oAlex.id, 1, 2))
        self.assertEqual(oModel.get_drag_info_from_path('0:1:0'),
                         (oHektor.abstractCard.id, oHektor.id, 1, 2))
        self.assertEqual(oModel.get_drag_info_from_path('0:3:0'),
                         (oEtienne.abstractCard.id, oEtienne.id, 1, 2))
        self.assertEqual(oModel.get_drag_info_from_path('0:0'),
                         (oAlex.abstractCard.id, None, 1, 1))
        self.assertEqual(oModel.get_drag_info_from_path('0:1'),
                         (oHektor.abstractCard.id, None, 1, 1))
        self.assertEqual(oModel.get_drag_info_from_path('0:3'),
                         (oEtienne.abstractCard.id, None, 1, 1))
        self.assertEqual(oModel.get_drag_info_from_path('0'),
                         (None, None, None, 0))
        # pylint: disable=protected-access
        # we need to access this protected methods
        oModel._change_level_mode(ExtraLevels.NO_SECOND_LEVEL)
        oModel.load()
        # This should also work for no expansions shown
        self.assertEqual(count_all_cards(oModel), 4)
        self.assertEqual(count_second_level(oModel), 0)
        self.assertEqual(oModel.get_drag_child_info('0'), {})
        self.assertEqual(oModel.get_drag_child_info('0:0'),
                         {oAlex.id: 1})
        self.assertEqual(oModel.get_drag_child_info('0:1'),
                         {oHektor.id: 1})
        self.assertEqual(oModel.get_drag_child_info('0:3'),
                         {oEtienne.id: 1})
        cleanup_models([oModel])

    def test_db_listeners(self):
        """Test that the model responds to changes to the card set hierarchy"""
        # We use an empty card set for these tests, to minimise time taken
        # pylint: disable=protected-access
        # we need to access protected methods
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oDummy = DummyCardSetController()
        oModel.set_controller(oDummy)
        oPCS2 = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        # Child tests
        self.assertEqual(oDummy.bReload, False)
        oPCS2.inuse = True
        self.assertEqual(oDummy.bReload, False)
        oModel._change_count_mode(ShowMode.CHILD_CARDS)
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
        oModel._change_count_mode(ShowMode.PARENT_CARDS)
        oModel._change_parent_count_mode(ParentCountMode.MINUS_SETS_IN_USE)
        oDummy.bReload = False
        oPCS3.inuse = False
        self.assertEqual(oDummy.bReload, True)
        oDummy.bReload = False
        oPCS.parent = None
        self.assertEqual(oDummy.bReload, True)
        oDummy.bReload = False
        oPCS3.inuse = True
        self.assertEqual(oDummy.bReload, False)
        cleanup_models([oModel])

    def test_config_listener(self):
        """Test that the model responds to the profile changes as expected"""
        # We use an empty card set for these tests, to minimise time taken
        # pylint: disable=protected-access
        # we need to access protected methods
        PhysicalCardSet(name=self.aNames[0])
        oModel = CardSetCardListModel(self.aNames[0], self.oConfig)
        oDummy = DummyCardSetController()
        oModel.set_controller(oDummy)
        sTestValue = list(SHOW_CARD_LOOKUP)[0]
        iTestMode = SHOW_CARD_LOOKUP[sTestValue]
        self.oConfig.set_profile_option(CARDSET, 'test', SHOW_CARD_OPTION,
                                        sTestValue)
        self.oConfig.set_profile_option(CARDSET, 'test2', SHOW_CARD_OPTION,
                                        sTestValue)
        # Check changing deck profile
        for sValue, iMode in SHOW_CARD_LOOKUP.items():
            iCurMode = oModel._eShowCardMode
            self.oConfig.set_profile_option(CARDSET, 'test', SHOW_CARD_OPTION,
                                            sValue)
            self.assertEqual(oModel._eShowCardMode, iCurMode)
            self.oConfig.set_profile(CARDSET, oModel.cardset_id, 'test')
            self.assertEqual(oModel._eShowCardMode, iMode)
            self.oConfig.set_profile(FRAME, oModel.frame_id, 'test2')
            self.assertEqual(oModel._eShowCardMode, iTestMode)
            self.oConfig.set_profile(FRAME, oModel.frame_id, 'defaults')
            self.oConfig.set_profile(CARDSET, oModel.cardset_id, 'defaults')
        # Check listener on card set profile changes
        self.oConfig.set_profile(CARDSET, oModel.cardset_id, 'test')
        self.oConfig.set_profile(FRAME, oModel.frame_id, 'test2')
        for sValue, iMode in EXTRA_LEVEL_LOOKUP.items():
            self.oConfig.set_profile_option(CARDSET, 'test',
                                            EXTRA_LEVEL_OPTION, sValue)
            self.assertEqual(oModel._eExtraLevelsMode, iMode)
        # Check listener on frame profile changes
        for sValue, iMode in PARENT_COUNT_LOOKUP.items():
            self.oConfig.set_profile_option(CARDSET, 'test2',
                                            PARENT_COUNT_MODE, sValue)
            self.assertEqual(oModel._eParentCountMode, iMode)
        # Check listener on local frame profile changes
        for sValue, iMode in PARENT_COUNT_LOOKUP.items():
            self.oConfig.set_local_frame_option(oModel.frame_id,
                                                PARENT_COUNT_MODE, sValue)
            self.assertEqual(oModel._eParentCountMode, iMode)
        cleanup_models([oModel])

    def _get_model(self, sName):
        """Return a model for the named card set, with the null grouping"""
        oModel = CardSetCardListModel(sName, self.oConfig)
        oModel.hideillegal = False
        oModel.groupby = NullGrouping
        return oModel

    def _setup_simple(self):
        """Convenience method for setting up a single card set for tests"""
        oPCS = PhysicalCardSet(name=self.aNames[0])
        aCards = [('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition')]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
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
        cleanup_models([oModel])

    def test_groupings(self):
        """Check over various groupings, single card set"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for cGrouping in (CryptLibraryGrouping, DisciplineGrouping,
                          ClanGrouping, CardTypeGrouping, ExpansionGrouping,
                          RarityGrouping):
            oModel = self._get_model(self.aNames[0])
            oModel.groupby = cGrouping
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        cleanup_models(aModels)

    def test_adding_filter(self):
        """Check adding cards with filters enabled (single card set)"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for oFilter in (BaseFilters.CardTypeFilter('Vampire'),
                        BaseFilters.PhysicalExpansionFilter('Sabbat'),
                        BaseFilters.CardSetMultiCardCountFilter(
                            (['2', '3'], self.aNames[0])),
                       ):
            oModel = self._get_model(self.aNames[0])
            oModel.selectfilter = oFilter
            oModel.applyfilter = True
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        cleanup_models(aModels)

    def test_adding_config_filter(self):
        """Check adding cards with config filter enabled (single card set)"""
        _oCache = SutekhObjectCache()
        oPCS = self._setup_simple()
        aModels = []
        for oFilter in (BaseFilters.CardTypeFilter('Vampire'),
                        BaseFilters.PhysicalExpansionFilter('Sabbat'),
                        BaseFilters.CardSetMultiCardCountFilter(
                            (['2', '3'], self.aNames[0])),
                       ):
            # pylint: disable=protected-access
            # we need to access protected methods
            oModel = self._get_model(self.aNames[0])
            oModel._oConfigFilter = oFilter
            aModels.append(oModel)
        self._loop_modes(oPCS, aModels)
        cleanup_models(aModels)

    def test_cache_simple(self):
        """Test that the special persistent caches don't affect results"""
        # pylint: disable=protected-access
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
            for iLevelMode in (ExtraLevels.NO_SECOND_LEVEL,
                               ExtraLevels.SHOW_EXPANSIONS):
                for oModel in aModels:
                    oModel._change_level_mode(iLevelMode)
                for iShowMode in (ShowMode.THIS_SET_ONLY, ShowMode.ALL_CARDS):
                    for oModel in aModels:
                        oModel._change_count_mode(iShowMode)
                        oModel.load()
                    for oCard in aCardsToAdd:
                        # pylint: disable=no-member
                        # SQLObject confuses pylint
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

        cleanup_models(aModels)

    def test_cache_complex(self):
        """Test that the special persistent caches don't affect results with
           more complex card set relationships"""
        # pylint: disable=protected-access, too-many-locals
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
            oModelCache._change_parent_count_mode(
                ParentCountMode.MINUS_SETS_IN_USE)
            aCache.append(oModelCache)
            oModelNoCache = self._get_model(sName)
            oModelNoCache._change_parent_count_mode(
                ParentCountMode.MINUS_SETS_IN_USE)
            aNoCache.append(oModelNoCache)
        aModels = aCache + aNoCache
        # See test_cache_simple
        aCardsToAdd = self.aPhysCards[1:8:2] + self.aPhysCards[9:]
        # We test a much smaller range of things than in loop_modes
        for bEditFlag in (False, True):
            for oModel in aModels:
                oModel.bEditable = bEditFlag
            for iLevelMode in (ExtraLevels.NO_SECOND_LEVEL,
                               ExtraLevels.SHOW_EXPANSIONS):
                for oModel in aModels:
                    oModel._change_level_mode(iLevelMode)
                for iShowMode in ShowMode:
                    for oModel in aModels:
                        oModel._change_count_mode(iShowMode)
                        oModel.load()
                    for oCS in (oEmptyPCS, oChildPCS, oGrandChildPCS, oPCS):
                        for oCard in aCardsToAdd:
                            # pylint: disable=no-member
                            # SQLObject confuses pylint
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
                                                     oModelNoCache,
                                                     'deleting')

        cleanup_models(aModels)

    def _setup_parent_child(self):
        """Setup the initial parent and child for relationship tests"""
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # Add cards
        aCards = [
            (u'Agent of Power', None), ('Alexandra', 'CE'),
            ('Sha-Ennu', 'Third Edition'),
            ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
            ('Alexandra', None), ('Bronwen', 'Sabbat'),
            ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
            ('Yvette, The Hopeless', 'CE'),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oPCS.addPhysicalCard(oCard.id)
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        for sName, sExp in aCards[2:6] + [(u'Two Wrongs', None)]:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oChildPCS.addPhysicalCard(oCard.id)
        oChildPCS.inuse = False

        oChildPCS.syncUpdate()
        oPCS.syncUpdate()
        return aCards, oPCS, oChildPCS

    def _setup_grand_child(self, aCards, oChildPCS):
        """Setup the grand child for the relationship tests"""
        oGrandChildPCS = PhysicalCardSet(name=self.aNames[2], parent=oChildPCS)
        for sName, sExp in aCards[3:7]:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oGrandChildPCS.addPhysicalCard(oCard.id)
        oGrandChildPCS.syncUpdate()
        return oGrandChildPCS

    def _setup_relationships(self):
        """Convenience method to setup a card set hierarchy for test cases"""
        aCards, oPCS, oChildPCS = self._setup_parent_child()
        oChildPCS.inuse = True
        oSibPCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS)
        for sName, sExp in aCards[1:6]:
            # pylint: disable=no-member
            # SQLObject confuses pylint
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
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oGrandChildPCS.addPhysicalCard(oCard.id)
        aGC2Cards = [
            ('AK-47', 'LotN'), ('Cesewayo', 'LoB'),
            ('Aire of Elation', 'CE'), ('Yvette, The Hopeless', None),
            ('Yvette, The Hopeless', 'BSC'), ('Ablative Skin', 'Sabbat'),
            ('Ablative Skin', None)
        ]
        for sName, sExp in aGC2Cards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
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
        cleanup_models(aModels)

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
        cleanup_models(aModels)

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
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oSibPCS.addPhysicalCard(oCard.id)
        oGrandChild2PCS = PhysicalCardSet(name=self.aNames[4],
                                          parent=oChildPCS)
        aCards = [
            ('AK-47', 'LotN'), ('Cesewayo', 'LoB'),
            ('Aire of Elation', 'CE'), ('Yvette, The Hopeless', None),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
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
        cleanup_models(aModels)

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
        cleanup_models(aModels)

    def test_relation_grouping(self):
        """Test groupings with complex relationships"""
        # Go through some of grouping tests as well
        # We want to ensure that this works with non-NullGroupings,
        # but we don't need to cover all the groupings again
        _oCache = SutekhObjectCache()
        _oPCS, _oSPCS, oChildPCS, _oGCPCS, _oGC2PCS = \
                self._setup_relationships()
        aModels = []
        for cGrouping in (DisciplineGrouping, CardTypeGrouping):
            for sName in self.aNames[:4]:
                oModel = self._get_model(sName)
                oModel.groupby = cGrouping
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        cleanup_models(aModels)

    def test_relation_filters(self):
        """Test adding with complex relationships and filters"""
        _oCache = SutekhObjectCache()
        _oPCS, _oSPCS, oChildPCS, _oGCPCS, _oGC2PCS = \
                self._setup_relationships()
        aModels = []
        for oFilter in (BaseFilters.CardTypeFilter('Vampire'),
                        BaseFilters.PhysicalExpansionFilter('Sabbat'),
                        BaseFilters.CardSetMultiCardCountFilter(
                            (['2', '3'], self.aNames[0])),
                       ):
            for sName in self.aNames[:4]:
                oModel = self._get_model(sName)
                oModel.selectfilter = oFilter
                oModel.applyfilter = True
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        cleanup_models(aModels)

    def test_relation_config_filters(self):
        """Test adding with complex relationships and the config filter
           enabled"""
        _oCache = SutekhObjectCache()
        _oPCS, _oSPCS, oChildPCS, _oGCPCS, _oGC2PCS = \
                self._setup_relationships()
        aModels = []
        for oFilter in (BaseFilters.CardTypeFilter('Vampire'),
                        BaseFilters.PhysicalExpansionFilter('Sabbat'),
                        BaseFilters.CardSetMultiCardCountFilter(
                            (['2', '3'], self.aNames[0])),
                       ):
            for sName in self.aNames[:4]:
                # pylint: disable=protected-access
                # we need to access protected methods
                oModel = self._get_model(sName)
                oModel._oConfigFilter = oFilter
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        cleanup_models(aModels)

    def test_rel_filter_cfg_filter(self):
        """Test with complex relationship, a physical config filter
           and additional filters"""
        _oCache = SutekhObjectCache()
        _oPCS, _oSPCS, oChildPCS, _oGCPCS, _oGC2PCS = \
                self._setup_relationships()
        aModels = []
        oConfigFilter = BaseFilters.CardSetMultiCardCountFilter(
            (['2', '3'], self.aNames[0]))
        for oFilter in (BaseFilters.CardTypeFilter('Vampire'),
                        BaseFilters.PhysicalExpansionFilter('Sabbat')):
            for sName in self.aNames[:4]:
                # pylint: disable=protected-access
                # we need to access protected methods
                oModel = self._get_model(sName)
                oModel._oConfigFilter = oConfigFilter
                oModel.selectfilter = oFilter
                oModel.applyfilter = True
                aModels.append(oModel)
        self._loop_modes(oChildPCS, aModels)
        cleanup_models(aModels)

    def test_filters(self):
        """Test filtering for the card set"""
        # pylint: disable=too-many-statements, protected-access
        # Want a long, sequential test case to reduce
        # repeated setups, so it has lots of lines
        # We need to access protected methods
        # Note that these tests are with the illegal card filter enabled
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        aCards = [
            ('Alexandra', 'CE', None), ('Sha-Ennu', 'Third', None),
            ('Hektor', 'Third Edition', 'Sketch'),
            ('Alexandra', None, None), ('Bronwen', 'Sabbat', None),
            ('.44 Magnum', 'Jyhad', None), ('.44 Magnum', 'Jyhad', None),
            ('Yvette, The Hopeless', 'CE', None),
            ('Yvette, The Hopeless', 'BSC', None)
        ]
        for sName, sExp, sPrint in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp, sPrint)
            oPCS.addPhysicalCard(oCard.id)
        oModel = self._get_model(self.aNames[0])
        # Test filter which selects nothing works
        self._loop_zero_filter_modes(oModel)
        # Check basic filtering
        oModel._change_count_mode(ShowMode.THIS_SET_ONLY)
        oModel._change_parent_count_mode(ParentCountMode.IGNORE_PARENT)
        oModel._change_level_mode(ExtraLevels.NO_SECOND_LEVEL)
        oModel.bEditable = False
        oModel.hideillegal = True
        # Test card type
        oModel.selectfilter = BaseFilters.CardTypeFilter('Vampire')
        oModel.applyfilter = True
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (1, 5, 0)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        oModel.groupby = DisciplineGrouping
        oModel.applyfilter = True
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (13, 23, 0)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        oModel._change_level_mode(ExtraLevels.SHOW_EXPANSIONS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (13, 23, 30)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        oModel.bEditable = True
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (13, 23, 63)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        # Add a child card set, and test filtering results
        oModel.groupby = NullGrouping
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS)
        # Do this to match how gui code works - this ensures that the
        # caches are cleared properly
        oChildPCS.inuse = True
        oChildPCS.syncUpdate()
        aCards = [
            ('Sha-Ennu', None),
            ('Kabede Maru', None),
            ('Gracis Nostinus', 'CE'),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oChildPCS.addPhysicalCard(oCard.id)
        oModel.bEditable = False
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (1, 5, 7)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        oModel._change_level_mode(ExtraLevels.SHOW_CARD_SETS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (1, 5, 2)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        oModel._change_count_mode(ShowMode.CHILD_CARDS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (1, 7, 4)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        oModel._change_count_mode(ShowMode.ALL_CARDS)
        oModel.load()
        tTotals = (oModel.iter_n_children(None),
                   count_all_cards(oModel),
                   count_second_level(oModel))
        tExpected = (1, 38, 4)
        self.assertEqual(tTotals, tExpected,
                         'Wrong results from filter : %s vs %s' % (
                             tTotals, tExpected))
        cleanup_models([oModel])

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
        aCards = [
            ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
            ('Alexandra', None), ('Bronwen', 'Sabbat'),
            ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
            ('Yvette, The Hopeless', 'CE'),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oPCS.addPhysicalCard(oCard.id)
            if sName != 'Yvette, The Hopeless':
                oGrandChildPCS.addPhysicalCard(oCard.id)
        self._loop_modes(oChildPCS, [oChildModel])
        cleanup_models([oChildModel])

    def test_reparenting_from_none(self):
        """Test corner cases around reparenting card sets.

           This tests reparenting a card set with no parent to
           having a parent"""
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # These will be reparented in the tests
        oChildPCS = PhysicalCardSet(name=self.aNames[1], inuse=True)
        oChild2PCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS,
                                     inuse=True)
        oModel = self._get_model(self.aNames[0])
        oChildModel = self._get_model(self.aNames[1])
        oChild2Model = self._get_model(self.aNames[3])
        # Add some cards to parent + child card sets
        aCards = [
            ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
            ('Alexandra', None), ('Bronwen', 'Sabbat'),
            ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
            ('Yvette, The Hopeless', 'CE'),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            if sName != 'Sha-Ennu':
                oPCS.addPhysicalCard(oCard.id)
            if sName != 'Yvette, The Hopeless':
                oChildPCS.addPhysicalCard(oCard.id)
                oChild2PCS.addPhysicalCard(oCard.id)
            if sName == '.44 Magnum':
                oChildPCS.addPhysicalCard(oCard.id)
                oChildPCS.addPhysicalCard(oCard.id)
        self._loop_modes_reparent(oPCS, oChildPCS,
                                  [oModel, oChildModel, oChild2Model])
        cleanup_models([oModel, oChildModel, oChild2Model])

    def test_reparenting_within_tree(self):
        """Test corner cases around reparenting card sets.

           This tests reparenting to a different point in the tree"""
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # These will be reparented in the tests
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS,
                                    inuse=True)
        oChild2PCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS,
                                     inuse=True)
        oModel = self._get_model(self.aNames[0])
        oChildModel = self._get_model(self.aNames[1])
        oChild2Model = self._get_model(self.aNames[3])
        # Add some cards to parent + child card sets
        aCards = [
            ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
            ('Alexandra', None), ('Bronwen', 'Sabbat'),
            ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
            ('Yvette, The Hopeless', 'CE'),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            if sName != 'Sha-Ennu':
                oPCS.addPhysicalCard(oCard.id)
            if sName != 'Yvette, The Hopeless':
                oChildPCS.addPhysicalCard(oCard.id)
                oChild2PCS.addPhysicalCard(oCard.id)
            if sName == '.44 Magnum':
                oChildPCS.addPhysicalCard(oCard.id)
                oChildPCS.addPhysicalCard(oCard.id)
        self._loop_modes_reparent(oChildPCS, oChild2PCS,
                                  [oModel, oChildModel, oChild2Model])
        cleanup_models([oModel, oChildModel, oChild2Model])

    def test_rename_child_card_set(self):
        """Test that we re-act to child card sets being renamed
           correctly"""
        # This basically tests that we clear the caches correctly,
        # since we turn the rename into a reload request
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        # Child card sets, to test rename logic
        oChildPCS = PhysicalCardSet(name=self.aNames[1], parent=oPCS,
                                    inuse=True)
        oChild2PCS = PhysicalCardSet(name=self.aNames[3], parent=oPCS,
                                     inuse=True)
        oChild3PCS = PhysicalCardSet(name=self.aNames[2], parent=oPCS,
                                     inuse=False)
        oModel = self._get_model(self.aNames[0])
        # Add some cards to parent + child card sets
        aCards = [
            ('Alexandra', 'CE'), ('Sha-Ennu', 'Third Edition'),
            ('Alexandra', None), ('Bronwen', 'Sabbat'),
            ('.44 Magnum', 'Jyhad'), ('.44 Magnum', 'Jyhad'),
            ('Yvette, The Hopeless', 'CE'),
            ('Yvette, The Hopeless', 'BSC')
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oChild3PCS.addPhysicalCard(oCard.id)
            if sName != 'Sha-Ennu':
                oPCS.addPhysicalCard(oCard.id)
            if sName != 'Yvette, The Hopeless':
                oChildPCS.addPhysicalCard(oCard.id)
                oChild2PCS.addPhysicalCard(oCard.id)
            if sName == '.44 Magnum':
                oChildPCS.addPhysicalCard(oCard.id)
                oChildPCS.addPhysicalCard(oCard.id)
        oPCS.syncUpdate()
        oChildPCS.syncUpdate()
        oChild2PCS.syncUpdate()
        oChild3PCS.syncUpdate()
        # Ensure we start with a clean cache
        oController = DummyCardSetController()
        oModel.set_controller(oController)
        oModel._dCache = {}

        oModel._change_count_mode(ShowMode.ALL_CARDS)
        oModel._change_level_mode(ExtraLevels.SHOW_CARD_SETS)
        oModel.load()

        aLoadList = get_all_counts(oModel)

        # rename the card set
        oChildPCS.name = "New child name"
        oChildPCS.syncUpdate()
        # Reload
        # We should have flagged a reload is required
        self.assertEqual(oController.bReload, True)
        oModel.load()
        oController.bReload = False
        aRenamedList = get_all_counts(oModel)

        # Manually rename the loaded list
        aManualList = []
        for tItem in aLoadList:
            tNewItem = (tItem[0], tItem[1],
                        tItem[2].replace(self.aNames[1], "New child name"))
            aManualList.append(tNewItem)

        # Model is unsorted, so we need to sort here
        self.assertEqual(sorted(aManualList), sorted(aRenamedList))

        # Check that a non-inuse rename doesn't trigger a reload request
        oChild3PCS.name = "New child 3 name"
        oChild3PCS.syncUpdate()
        self.assertEqual(oController.bReload, False)

        cleanup_models([oModel])

    def test_postfix(self):
        """Test the behaviour of using the '..., the' postfix option"""
        _oCache = SutekhObjectCache()
        oPCS = PhysicalCardSet(name=self.aNames[0])
        oModel = self._get_model(self.aNames[0])

        aCards = [
            ('Alexandra', 'CE'),
            ('The Ankara Citadel, Turkey', 'CE'),
            ('An Anarch Manifesto', 'TR'),
            ('Anson', 'Jyhad'),
            ('The Path of Blood', 'FN'),
            ('Raven Spy', 'LotN'),
            ('Ossian', 'KMW'),
            ('Walk of Flame', 'Jyhad'),
        ]
        for sName, sExp in aCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCard = make_card(sName, sExp)
            oPCS.addPhysicalCard(oCard.id)
        oPCS.syncUpdate()

        oController = DummyCardSetController()
        oModel.set_controller(oController)
        oModel._dCache = {}

        oModel._change_count_mode(ShowMode.THIS_SET_ONLY)
        oModel._change_level_mode(ExtraLevels.NO_SECOND_LEVEL)
        # These tests require sorted results
        oModel.enable_sorting()
        oModel.load()

        aNormal = get_all_counts(oModel)

        self.assertEqual(aNormal,
                         [(8, 0, 'All'),
                          (1, 0, 'All:Alexandra'),
                          (1, 0, 'All:An Anarch Manifesto'),
                          (1, 0, 'All:Anson'),
                          (1, 0, 'All:Ossian'),
                          (1, 0, 'All:Raven Spy'),
                          (1, 0, 'All:The Ankara Citadel, Turkey'),
                          (1, 0, 'All:The Path of Blood'),
                          (1, 0, 'All:Walk of Flame'),
                         ])
        # Change the postfix mode
        self.oConfig.set_postfix_the_display(True)
        # We shouldn't need to reload anything becau
        aPostfix = get_all_counts(oModel)
        self.assertEqual(aPostfix,
                         [(8, 0, 'All'),
                          (1, 0, 'All:Alexandra'),
                          (1, 0, 'All:Anarch Manifesto, An'),
                          (1, 0, 'All:Ankara Citadel, Turkey, The'),
                          (1, 0, 'All:Anson'),
                          (1, 0, 'All:Ossian'),
                          (1, 0, 'All:Path of Blood, The'),
                          (1, 0, 'All:Raven Spy'),
                          (1, 0, 'All:Walk of Flame'),
                         ])
        # Check that it is preserved across reloads
        oModel.load()
        aReload = get_all_counts(oModel)
        self.assertEqual(aPostfix, aReload)
        # Check that new entries are handled correctly
        oCard = make_card('The SlaughterHouse', 'LoB')
        for _iCnt in range(2):
            oPCS.addPhysicalCard(oCard.id)
            oPCS.syncUpdate()
            send_changed_signal(oPCS, oCard, 1)
        aUpdated = get_all_counts(oModel)
        self.assertEqual(aUpdated,
                         [(10, 0, 'All'),
                          (1, 0, 'All:Alexandra'),
                          (1, 0, 'All:Anarch Manifesto, An'),
                          (1, 0, 'All:Ankara Citadel, Turkey, The'),
                          (1, 0, 'All:Anson'),
                          (1, 0, 'All:Ossian'),
                          (1, 0, 'All:Path of Blood, The'),
                          (1, 0, 'All:Raven Spy'),
                          (2, 0, 'All:Slaughterhouse, The'),
                          (1, 0, 'All:Walk of Flame'),
                         ])
        # Check that unsetting the option behaves as expected
        self.oConfig.set_postfix_the_display(False)
        aNormal = get_all_counts(oModel)
        self.assertEqual(aNormal,
                         [(10, 0, 'All'),
                          (1, 0, 'All:Alexandra'),
                          (1, 0, 'All:An Anarch Manifesto'),
                          (1, 0, 'All:Anson'),
                          (1, 0, 'All:Ossian'),
                          (1, 0, 'All:Raven Spy'),
                          (1, 0, 'All:The Ankara Citadel, Turkey'),
                          (1, 0, 'All:The Path of Blood'),
                          (2, 0, 'All:The Slaughterhouse'),
                          (1, 0, 'All:Walk of Flame'),
                         ])


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
