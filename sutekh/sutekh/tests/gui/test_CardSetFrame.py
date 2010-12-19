# test_CardSetFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test parts of the card set controller-view-model interactions"""

from sutekh.tests.GuiSutekhTest import GuiSutekhTest
import unittest
import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCard, \
        IAbstractCard
from sutekh.tests.core.test_Filters import make_card


class TestCardSetFrame(GuiSutekhTest):
    """Class for the CardSetFrame test cases"""

    # pylint: disable-msg=R0201
    # I prefer to have these as methods

    def _select_cards(self, oFrame, aCards):
        """Find cards by name and expansion in the frame and select them"""
        oModel = oFrame.view.get_model()
        oSelection = oFrame.view.get_selection()
        oFrame.view.expand_all()  # needed so we can select deeper entries
        oSelection.unselect_all()
        # Walk the model, tracking the paths we wish to select
        oIter = oModel.get_iter_root()
        while oIter:
            # loop over card level nodes
            oCardIter = oModel.iter_children(oIter)
            while oCardIter:
                # Loop over expansions
                sName = oModel.get_name_from_iter(oCardIter)
                if (sName, 'Top Level') in aCards:
                    oPath = oModel.get_path(oCardIter)
                    oSelection.select_path(oPath)
                oExpIter = oModel.iter_children(oCardIter)
                while oExpIter:
                    sExp = oModel.get_name_from_iter(oExpIter)
                    if sExp == oModel.sUnknownExpansion:
                        sExp = None
                    if ((sName, sExp) in aCards):
                        oPath = oModel.get_path(oExpIter)
                        oSelection.select_path(oPath)
                    oExpIter = oModel.iter_next(oExpIter)
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

    # pylint: enable-msg=R0201

    def test_basic(self):
        """Set of simple tests of the CardSetFrame"""
        # pylint: disable-msg=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables

        # Add card sets needed for the tests
        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint
        oPhysCardSet = PhysicalCardSet(name='My Collection')
        oPCS2 = PhysicalCardSet(name='Test Set 1',
                parent=oPhysCardSet)
        # Add some cards
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')] + [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = make_card(sName, sExp)
            aPhysCards.append(oCard)
        for oCard in aPhysCards:
            oPhysCardSet.addPhysicalCard(oCard.id)
            oPhysCardSet.syncUpdate()
        self.oWin.setup(self.oConfig)
        # Remove the unneeded panes
        for oPane in self.oWin.aOpenFrames[:]:
            if oPane.title in ('Card Text', 'Card Set List'):
                self.oWin.remove_frame(oPane)
            if oPane.title == 'White Wolf Card List':
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
        # Select cards in new card set and change numbers
        self._select_cards(oNewFrame, [(u'AK-47', None),
                (u'AK-47', u'Lords of the Night')])
        # Generate key_press event
        oEvent = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        oEvent.keyval = int(gtk.gdk.keyval_from_name('4'))
        oNewFrame.view.key_press(oNewFrame, oEvent)
        self.assertEqual(len(oPCS2.cards), 8)
        oNewFrame.view.key_press(oNewFrame, oEvent)
        self.assertEqual(len(oPCS2.cards), 8)
        oEvent.keyval = int(gtk.gdk.keyval_from_name('1'))
        oNewFrame.view.key_press(oNewFrame, oEvent)
        self.assertEqual(len(oPCS2.cards), 2)
        oEvent.keyval = int(gtk.gdk.keyval_from_name('plus'))
        oNewFrame.view.key_press(oNewFrame, oEvent)
        self.assertEqual(len(oPCS2.cards), 4)
        oEvent.keyval = int(gtk.gdk.keyval_from_name('minus'))
        oNewFrame.view.key_press(oNewFrame, oEvent)
        self.assertEqual(len(oPCS2.cards), 2)
        oNewFrame.view.key_press(oNewFrame, oEvent)
        self.assertEqual(len(oPCS2.cards), 0)
        # Select all and delete it from the new card set
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 2)
        self._select_cards(oNewFrame, [(u'AK-47', u'Lords of the Night')])
        oNewFrame.view.del_selection()
        self.assertEqual(len(oPCS2.cards), 1)
        self._select_cards(oNewFrame, [(u'AK-47', None)])
        oEvent.keyval = int(gtk.gdk.keyval_from_name('plus'))
        oNewFrame.view.key_press(oNewFrame, oEvent)
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
        self._select_cards(oFrame, [(u'AK-47', 'Top Level'),
            (u'Ablative Skin', 'Top Level')])
        oFrame.view.copy_selection()
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 11)
        self.assertEqual(len([x for x in oPCS2.cards if
            IAbstractCard(x).name == 'Alexandra']), 5)
        self.assertEqual(len([x for x in oPCS2.cards if
            IAbstractCard(x).name == 'AK-47']), 4)
        aCardNames = [oCard.abstractCard.name for oCard in oPCS2.cards]
        self._select_cards(oNewFrame, [(sName, 'Top Level') for sName in
            aCardNames])
        oNewFrame.view.del_selection()
        self.assertEqual(len(oPCS2.cards), 0)
        oFrame = oMyColl
        self._select_cards(oFrame, [(u'AK-47', 'Top Level'),
            (u'Ablative Skin', 'Top Level')])
        oFrame.view.copy_selection()
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 7)
        self.assertEqual(len([x for x in oPCS2.cards if
            IAbstractCard(x).name == 'AK-47']), 1)
        self.assertEqual(len([x for x in oPCS2.cards if
            IAbstractCard(x).name == 'Ablative Skin']), 6)
        self.assertEqual(len([x for x in oPCS2.cards if
            IAbstractCard(x).name == 'Ablative Skin' and
            IPhysicalCard(x).expansionID is None]), 5)
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


if __name__ == "__main__":
    unittest.main()
