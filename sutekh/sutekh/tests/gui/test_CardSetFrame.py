# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test parts of the card set controller-view-model interactions"""

import unittest

from gi.repository import Gdk

from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.BaseAdapters import (IPhysicalCard, IAbstractCard,
                                           IPrintingName)
from sutekh.base.core import BaseFilters
from sutekh.base.tests.TestUtils import make_card
from sutekh.base.gui.BaseConfigFile import CARDSET
from sutekh.base.gui.CardSetListModel import EXTRA_LEVEL_OPTION

from sutekh.tests.GuiSutekhTest import GuiSutekhTest


class TestCardSetFrame(GuiSutekhTest):
    """Class for the CardSetFrame test cases"""
    # pylint: disable=too-many-public-methods
    # tunittest.TestCase, so many public methods

    # pylint: disable=no-self-use
    # I prefer to have these as methods

    def _select_cards(self, oFrame, aCards):
        """Find cards by name and extra levels in the frame and select them"""
        def do_level_select(oSelection, oModel, tBase, oIter, aCards):
            """Handle the selection logic for the current level"""
            sVal = oModel.get_name_from_iter(oIter)
            if sVal == oModel.sUnknownExpansion:
                sVal = None
            if tBase + (sVal, ) in aCards:
                oPath = oModel.get_path(oIter)
                oSelection.select_path(oPath)
            return sVal
        oModel = oFrame.view.get_model()
        oSelection = oFrame.view.get_selection()
        oFrame.view.expand_all()  # needed so we can select deeper entries
        oSelection.unselect_all()
        # Walk the model, tracking the paths we wish to select
        oIter = oModel.get_iter_first()
        while oIter:
            # loop over card level nodes
            oCardIter = oModel.iter_children(oIter)
            while oCardIter:
                # Loop over expansions
                sName = do_level_select(oSelection, oModel, (), oCardIter,
                                        aCards)
                oSecondIter = oModel.iter_children(oCardIter)
                while oSecondIter:
                    sSecond = do_level_select(oSelection, oModel, (sName, ),
                                              oSecondIter, aCards)
                    oThirdIter = oModel.iter_children(oSecondIter)
                    while oThirdIter:
                        do_level_select(oSelection, oModel, (sName, sSecond),
                                        oThirdIter, aCards)
                        oThirdIter = oModel.iter_next(oThirdIter)
                    oSecondIter = oModel.iter_next(oSecondIter)
                oCardIter = oModel.iter_next(oCardIter)
            oIter = oModel.iter_next(oIter)

    def check_row(self, _oModel, oPath, _oIter, tInfo):
        """Add a row to the list if it's expanded"""
        oView, aPaths = tInfo
        if oView.row_expanded(oPath):
            aPaths.append(oPath)

    def get_expanded(self, oView):
        """Get the expanded entries from the view"""
        aPaths = []
        oView.get_model().foreach(self.check_row, (oView, aPaths))
        aPaths.sort()
        return aPaths

    # pylint: enable=no-self-use

    def test_basic(self):
        """Set of simple tests of the CardSetFrame"""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables

        # Add card sets needed for the tests
        # pylint: disable=unsupported-membership-test, not-an-iterable
        # Checks on RelatedJoins confuse pylint
        oPhysCardSet = PhysicalCardSet(name='My Collection')
        oPCS2 = PhysicalCardSet(name='Test Set 1',
                                parent=oPhysCardSet)
        # Add some cards
        aCards = [
            ('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
            ('Anna "Dictatrix11" Suljic', 'NoR'),
            ('Ablative Skin', 'Sabbat')
        ] + [('Alexandra', 'CE'), ('Alexandra', None),
             ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            aPhysCards.append(oCard)
        for oCard in aPhysCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oPhysCardSet.addPhysicalCard(oCard.id)
            oPhysCardSet.syncUpdate()
        self.oWin.setup(self.oConfig)
        # Remove the unneeded panes
        for oPane in self.oWin.aOpenFrames[:]:
            if oPane.title in ('Card Text', 'Card Set List'):
                self.oWin.remove_frame(oPane)
            if oPane.title == 'Full Card List':
                oWWList = oPane
            if oPane.title == 'My Collection':
                oMyColl = oPane
        # Add a set, not opened editable
        oNewFrame = self.oWin.add_new_physical_card_set('Test Set 1', False)
        # Add one of the new card sets, as an empty, editable set
        # Create selection of cards from the WW card list and
        # paste it into the new card set
        oFrame = oWWList
        self._select_cards(oFrame, [(u'AK-47', None),
                                    (u'AK-47', u'Lords of the Night')])
        self.assertEqual(oFrame.view.get_selection().count_selected_rows(), 2)
        # Copy
        oFrame.view.copy_selection()
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 0)
        self.oWin.remove_frame(oNewFrame)
        # Reopen the card set, only editable this time
        oNewFrame = self.oWin.add_new_physical_card_set('Test Set 1', True)
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 2)
        # Check we've pasted the right cards
        self.assertTrue(make_card(u'AK-47', None) in oPCS2.cards)
        self.assertTrue(make_card(u'AK-47', u'Lords of the Night')
                        in oPCS2.cards)
        # Select cards in new card set and change numbers
        self._select_cards(oNewFrame, [(u'AK-47', None),
                                       (u'AK-47', u'Lords of the Night')])
        # Generate key_press event
        oEvent = Gdk.Event()
        oEvent.type = Gdk.EventType.KEY_PRESS
        oEvent.key.keyval = int(Gdk.keyval_from_name('4'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 8)
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 8)
        oEvent.key.keyval = int(Gdk.keyval_from_name('1'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 2)
        oEvent.key.keyval = int(Gdk.keyval_from_name('plus'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 4)
        oEvent.key.keyval = int(Gdk.keyval_from_name('minus'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 2)
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 0)
        # Select all and delete it from the new card set
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 2)
        self._select_cards(oNewFrame, [(u'AK-47', u'Lords of the Night')])
        oNewFrame.view.del_selection()
        self.assertEqual(len(oPCS2.cards), 1)
        self._select_cards(oNewFrame, [(u'AK-47', None)])
        oEvent.key.keyval = int(Gdk.keyval_from_name('plus'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 2)
        oNewFrame.view.del_selection()
        self.assertEqual(len(oPCS2.cards), 0)
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 2)
        # Select card from My Collection and paste it into the card set
        oFrame = oMyColl
        # set editable off
        oNewFrame.view.toggle_editable(False)
        # Verify that trying to paste the selection does nothing
        self._select_cards(oFrame, [(u'AK-47', None),
                                    ('Ablative Skin', 'Sabbat'),
                                    ('Alexandra', 'Camarilla Edition')])
        oFrame.view.copy_selection()
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 2)
        # set editable on and verify that we can change the numbers
        oNewFrame.view.toggle_editable(True)
        oNewFrame.view.do_paste()
        # We should get 5 copies of Alexandra from My Collection
        self.assertEqual(len(oPCS2.cards), 9)
        self.assertEqual(len([x for x in oPCS2.cards if
                              IAbstractCard(x).name == 'Alexandra']), 5)
        # Tests involving the top level selection
        oFrame = oWWList
        self._select_cards(oFrame, [(u'AK-47', ),
                                    (u'Ablative Skin', )])
        oFrame.view.copy_selection()
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 11)
        self.assertEqual(len([x for x in oPCS2.cards if
                              IAbstractCard(x).name == 'Alexandra']), 5)
        self.assertEqual(len([x for x in oPCS2.cards if
                              IAbstractCard(x).name == 'AK-47']), 4)
        aCardNames = [oCard.abstractCard.name for oCard in oPCS2.cards]
        self._select_cards(oNewFrame, [(sName, ) for sName in
                                       aCardNames])
        oNewFrame.view.del_selection()
        self.assertEqual(len(oPCS2.cards), 0)
        oFrame = oMyColl
        self._select_cards(oFrame, [(u'AK-47', ),
                                    (u'Ablative Skin', )])
        oFrame.view.copy_selection()
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 7)
        self.assertEqual(len([x for x in oPCS2.cards if
                              IAbstractCard(x).name == 'AK-47']), 1)
        self.assertEqual(len([x for x in oPCS2.cards if
                              IAbstractCard(x).name == 'Ablative Skin']), 6)
        self.assertEqual(len([x for x in oPCS2.cards if
                              IAbstractCard(x).name == 'Ablative Skin' and
                              IPhysicalCard(x).printingID is None]), 5)
        # Test involving top level and sublevel selections
        # Top level should override the sub selections, as being
        # most consitent behaviour
        self._select_cards(oNewFrame, [(u'AK-47', ),
                                       (u'AK-47', None),
                                       (u'AK-47', 'Lords of the Night')])
        oEvent = Gdk.Event()
        oEvent.type = Gdk.EventType.KEY_PRESS
        oEvent.key.keyval = int(Gdk.keyval_from_name('4'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 10)
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 10)
        oEvent.key.keyval = int(Gdk.keyval_from_name('1'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 7)
        oEvent.key.keyval = int(Gdk.keyval_from_name('plus'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 8)
        oEvent.key.keyval = int(Gdk.keyval_from_name('minus'))
        oNewFrame.view.key_press(oNewFrame, oEvent.key)
        self.assertEqual(len(oPCS2.cards), 7)
        # We should copy all the ones from My Collection
        # rename card set, and verify that everything gets updated properly

        # Check reload keep expanded works
        aExp1 = self.get_expanded(oFrame.view)
        oFrame.reload()
        aExp2 = self.get_expanded(oFrame.view)
        self.assertEqual(aExp1, aExp2)
        # Change some paths
        oFrame.view.collapse_all()
        for oPath in aExp1[::4]:
            oFrame.view.expand_to_path(oPath)
        aExp1 = self.get_expanded(oFrame.view)
        self.assertNotEqual(aExp1, aExp2)  # We have changed the paths
        oFrame.reload()
        aExp2 = self.get_expanded(oFrame.view)
        self.assertEqual(aExp1, aExp2)  # But reload has retained the new state

    def test_delete_with_physical_filters(self):
        """Test deleting cards with physical filters in play."""
        oColl = PhysicalCardSet(name='My Collection')
        # Add some cards
        aCards = [("Ghoul Retainer", "Jyhad", None)] * 2 + \
            [("Ghoul Retainer", "Jyhad", "Variant Printing")] * 3 + \
            [("Off Kilter", "HttB", None)] * 3 + \
            [("Off Kilter", "HttB", "No Draft Text")] * 4
        aPhysCards = []
        for (sName, sExp, sPrint) in aCards:
            oCard = make_card(sName, sExp, sPrint)
            aPhysCards.append(oCard)
        for oCard in aPhysCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oColl.addPhysicalCard(oCard.id)
            oColl.syncUpdate()
        self.assertEqual(len(oColl.cards), 12)
        self.oWin.setup(self.oConfig)
        # Remove the unneeded panes
        for oPane in self.oWin.aOpenFrames[:]:
            if oPane.title in ('Card Text', 'Card Set List', 'Full Card List'):
                self.oWin.remove_frame(oPane)
            if oPane.title == 'My Collection':
                oMyColl = oPane
        oMyColl.view.toggle_editable(True)
        # Test deleting with no filter works as expected
        self._select_cards(oMyColl, [(u'Ghoul Retainer', ),
                                     (u'Off Kilter', )])
        oEvent = Gdk.Event()
        oEvent.type = Gdk.EventType.KEY_PRESS
        oEvent.key.keyval = int(Gdk.keyval_from_name('minus'))
        # Check that we can delete all the way
        # We should remove 2 cards each time until we've removed
        # 5 Ghoul Retainers
        for iExpected in range(10, 0, -2):
            oMyColl.view.key_press(oMyColl, oEvent.key)
            self.assertEqual(len(oColl.cards), iExpected)
        # Then remove 1 card for the last 2
        for iExpected in range(1, -1, -1):
            oMyColl.view.key_press(oMyColl, oEvent.key)
            self.assertEqual(len(oColl.cards), iExpected)
        oColl.syncUpdate()
        for oCard in aPhysCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oColl.addPhysicalCard(oCard.id)
            oColl.syncUpdate()
        self.assertEqual(len(oColl.cards), 12)
        oMyColl.reload()
        # Test deleting with physical printing filter works as expected
        oFilter = BaseFilters.PhysicalPrintingFilter(
            'Jyhad (Variant Printing)')
        oMyColl.view.set_filter(oFilter)
        oMyColl.reload()
        self._select_cards(oMyColl, [(u'Ghoul Retainer', )])
        # Each removal should remove 1 card
        for iExpected in range(11, 8, -1):
            oMyColl.view.key_press(oMyColl, oEvent.key)
            self.assertEqual(len(oColl.cards), iExpected)
        # Further removals have no effect
        oMyColl.view.key_press(oMyColl, oEvent.key)
        self.assertEqual(len(oColl.cards), 9)
        oMyColl.view.key_press(oMyColl, oEvent.key)
        self.assertEqual(len(oColl.cards), 9)
        # Test deleting with physical expansion filter works as expected
        oFilter = BaseFilters.PhysicalExpansionFilter('Heirs to the Blood')
        oMyColl.view.set_filter(oFilter)
        oMyColl.reload()
        self._select_cards(oMyColl, [(u'Off Kilter', )])
        for iExpected in range(8, 1, -1):
            oMyColl.view.key_press(oMyColl, oEvent.key)
            self.assertEqual(len(oColl.cards), iExpected)
        # Asset that all the remaining 2 cards are both Jyhad (No variant)
        # Ghoul retainers
        # pylint: disable=not-an-iterable
        # SQLObject confuses pylint here
        for oCard in oColl.cards:
            self.assertEqual(oCard.abstractCard.name, "Ghoul Retainer")
            self.assertEqual(IPrintingName(oCard), "Jyhad")

    def test_paste_form_card_set(self):
        """Test selecting and pasting with the different display modes"""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        # Add card sets needed for the tests
        # pylint: disable=unsupported-membership-test, not-an-iterable
        # Checks on RelatedJoins confuse pylint

        def clear_cardset(oPCS, oFrame):
            """Clear the cards from a card set and reload the model"""
            for oCard in oPCS.cards:
                oPCS.removePhysicalCard(oCard)
            oFrame.view.get_model().load()

        oCollSet = PhysicalCardSet(name='My Collection')
        oTest1 = PhysicalCardSet(name='Test Set 1',
                                 parent=oCollSet,
                                 inuse=True)
        # Add some cards
        aCards = [
            ('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
            ('AK-47', 'Lords of the Night'),
            ('AK-47', 'Lords of the Night'),
            ('Anna "Dictatrix11" Suljic', 'NoR'),
            ('Ablative Skin', 'Sabbat')
        ] + [('Alexandra', 'CE'), ('Alexandra', None),
             ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            aPhysCards.append(oCard)
        for oCard in aPhysCards:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oCollSet.addPhysicalCard(oCard.id)
            oCollSet.syncUpdate()
        oAKLotN = make_card(u'AK-47', u'Lords of the Night')
        oAKNone = make_card(u'AK-47', None)
        oAblative = make_card(u'Ablative Skin', None)
        oAlex = make_card(u'Alexandra', u'CE')
        for oCard in [oAKLotN, oAKLotN, oAKLotN,
                      oAKNone, oAKNone,
                      make_card(u'Ablative Skin', 'Sabbat'),
                      oAblative, oAblative, oAblative, oAblative, oAblative,
                      oAlex, oAlex, oAlex]:
            # pylint: disable=no-member
            # SQLObject confuses pylint
            oTest1.addPhysicalCard(oCard.id)
            oTest1.syncUpdate()
        self.oWin.setup(self.oConfig)
        # Remove the unneeded panes
        for oPane in self.oWin.aOpenFrames[:]:
            if oPane.title in ('Card Text', 'Card Set List', 'Full Card List'):
                self.oWin.remove_frame(oPane)
            if oPane.title == 'My Collection':
                oMyColl = oPane
        # Create the test profile and use it to set "My Collection"
        # to 'No Children'
        self.oConfig.set_profile_option(CARDSET, "test",
                                        EXTRA_LEVEL_OPTION, "none")
        self.oConfig.set_profile(CARDSET, oMyColl.view.get_model().cardset_id,
                                 'test')
        self.oWin.do_all_queued_reloads()
        # Create a new set to paste into
        oTest2 = PhysicalCardSet(name='Test Set 2')
        oCS2Frame = self.oWin.add_new_physical_card_set('Test Set 2', True)
        # Select 2 cards and paste them
        self._select_cards(oMyColl, [(u'AK-47', ),
                                     (u'Ablative Skin', )])
        oMyColl.view.copy_selection()
        oCS2Frame.view.do_paste()
        # 3 x AK + 6 x Ablative
        self.assertEqual(len(oTest2.cards), 9)
        # Selecting these should match the expansions in My Collection
        self.assertEqual(len([x for x in oTest2.cards if x == oAKLotN]), 2)
        self.assertEqual(len([x for x in oTest2.cards if x == oAKNone]), 1)
        self.assertEqual(len([x for x in oTest2.cards if x == oAblative]), 5)
        self.assertTrue(make_card(u'Ablative Skin', 'Sabbat') in oTest2.cards)
        # Remove cards from test card set
        clear_cardset(oTest2, oCS2Frame)
        self.assertEqual(len(oTest2.cards), 0)
        # Change mode to expansions
        self.oConfig.set_profile_option(CARDSET, "test",
                                        EXTRA_LEVEL_OPTION, "expansions")
        self.oWin.do_all_queued_reloads()
        self._select_cards(oMyColl, [(u'AK-47', u'Lords of the Night'),
                                     (u'Ablative Skin', ),
                                     (u'Alexandra', u'Camarilla Edition')])
        oMyColl.view.copy_selection()
        oCS2Frame.view.do_paste()
        # 2 x AK + 6 x Ablative + 5 x Alexandra
        self.assertEqual(len(oTest2.cards), 13)
        self.assertTrue(make_card(u'Ablative Skin', 'Sabbat') in oTest2.cards)
        self.assertEqual(len([x for x in oTest2.cards if x == oAKLotN]), 2)
        self.assertEqual(len([x for x in oTest2.cards if x == oAblative]), 5)
        self.assertEqual(len([x for x in oTest2.cards if x == oAlex]), 5)
        clear_cardset(oTest2, oCS2Frame)
        self.assertEqual(len(oTest2.cards), 0)
        # Change mode to card sets
        self.oConfig.set_profile_option(CARDSET, "test",
                                        EXTRA_LEVEL_OPTION, "card sets")
        self.oWin.do_all_queued_reloads()
        oMyColl.view.get_model().load()
        self._select_cards(oMyColl, [(u'AK-47', u'Test Set 1'),
                                     (u'Ablative Skin', ),
                                     (u'Alexandra', u'Test Set 1')])
        oMyColl.view.copy_selection()
        oCS2Frame.view.do_paste()
        # 5 x AK + 6 x Ablative + 3 x Alexandra
        self.assertEqual(len(oTest2.cards), 14)
        self.assertTrue(make_card(u'Ablative Skin', 'Sabbat') in oTest2.cards)
        self.assertEqual(len([x for x in oTest2.cards if x == oAKLotN]), 3)
        self.assertEqual(len([x for x in oTest2.cards if x == oAKNone]), 2)
        self.assertEqual(len([x for x in oTest2.cards if x == oAblative]), 5)
        self.assertEqual(len([x for x in oTest2.cards if x == oAlex]), 3)
        clear_cardset(oTest2, oCS2Frame)
        self.assertEqual(len(oTest2.cards), 0)
        # Change mode to card sets & expansions
        self.oConfig.set_profile_option(CARDSET, "test",
                                        EXTRA_LEVEL_OPTION,
                                        "card sets then expansions")
        self.oWin.do_all_queued_reloads()
        self._select_cards(oMyColl, [(u'AK-47', u'Test Set 1',
                                      u'Lords of the Night'),
                                     (u'Ablative Skin', ),
                                     (u'Alexandra', u'Test Set 1')])
        oMyColl.view.copy_selection()
        oCS2Frame.view.do_paste()
        # 3 x AK + 6 x Ablative + 3 x Alexandra
        self.assertEqual(len(oTest2.cards), 12)
        self.assertTrue(make_card(u'Ablative Skin', 'Sabbat') in oTest2.cards)
        self.assertEqual(len([x for x in oTest2.cards if x == oAKLotN]), 3)
        self.assertEqual(len([x for x in oTest2.cards if x == oAblative]), 5)
        self.assertEqual(len([x for x in oTest2.cards if x == oAlex]), 3)

        clear_cardset(oTest2, oCS2Frame)
        self.assertEqual(len(oTest2.cards), 0)
        # Change mode to expansions & card sets
        self.oConfig.set_profile_option(CARDSET, "test",
                                        EXTRA_LEVEL_OPTION,
                                        "expansions then card sets")
        self.oWin.do_all_queued_reloads()
        self._select_cards(oMyColl, [(u'AK-47', u'Lords of the Night'),
                                     (u'Ablative Skin', ),
                                     (u'Alexandra', u'Camarilla Edition',
                                      u'Test Set 1')])
        oMyColl.view.copy_selection()
        oCS2Frame.view.do_paste()
        # 2 x AK + 6 x Ablative + 3 x Alexandra
        self.assertEqual(len(oTest2.cards), 11)
        self.assertTrue(make_card(u'Ablative Skin', 'Sabbat') in oTest2.cards)
        self.assertEqual(len([x for x in oTest2.cards if x == oAKLotN]), 2)
        self.assertEqual(len([x for x in oTest2.cards if x == oAblative]), 5)
        self.assertEqual(len([x for x in oTest2.cards if x == oAlex]), 3)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
