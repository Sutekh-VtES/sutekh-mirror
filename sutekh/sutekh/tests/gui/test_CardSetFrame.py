# test_CardSetFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test parts of the card set controller-view-model interactions"""

from sutekh.tests.TestCore import SutekhTest
from nose import SkipTest
import gtk
import unittest
from sutekh.core.SutekhObjects import PhysicalCardSet, IExpansion, \
        IAbstractCard, IPhysicalCard
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.gui.ConfigFile import ConfigFile

class TestCardSetFrame(SutekhTest):
    """Class for the MultiPanewindow test cases"""

    def _gen_card(self, sName, sExp):
        """Create a card given the name and Expansion"""
        if sExp:
            oExp = IExpansion(sExp)
        else:
            oExp = None
        oAbs = IAbstractCard(sName)
        return IPhysicalCard((oAbs, oExp))

    def _select_cards(self, oFrame, aCards):
        """Find cards by name and expansion in the frame and select them"""
        oModel = oFrame._oController.model
        oSelection = oFrame.view.get_selection()
        oFrame.view.expand_all() # needed so we can select deeper entries
        # Walk the model, tracking the paths we wish to select
        oIter = oModel.get_iter_root()
        while oIter:
            # loop over card level nodes
            oCardIter = oModel.iter_children(oIter)
            while oCardIter:
                # Loop over expansions
                sName = oModel.get_name_from_iter(oCardIter)
                oExpIter = oModel.iter_children(oCardIter)
                while oExpIter:
                    sExp = oModel.get_name_from_iter(oExpIter)
                    if sExp == oModel.sUnknownExpansion:
                        sExp = None
                    if ((sName, sExp) in aCards):
                        oPath=oModel.get_path(oExpIter)
                        oSelection.select_path(oPath)
                    oExpIter = oModel.iter_next(oExpIter)
                oCardIter = oModel.iter_next(oCardIter)
            oIter = oModel.iter_next(oIter)

    def test_basic(self):
        """Set of simple tests of the CardSetFrame"""
        # Skip if we're not under a windowing system
        # We need to do this before trying to run MultiPaneWindow's __init__,
        # which will fail if not under a windowing system
        if gtk.gdk.screen_get_default() is None:
            raise SkipTest
        # Add card sets needed for the tests
        oPhysCardSet = PhysicalCardSet(name='My Collection')
        oPCS2 = PhysicalCardSet(name='Test Set 1',
                parent=oPhysCardSet)
        PhysicalCardSet(name='Test Set 2',
                parent=oPhysCardSet)
        # Add some cards
        aCards = [('AK-47', None), ('Bronwen', 'SW'), ('Cesewayo', None),
                ('Anna "Dictatrix11" Suljic', 'NoR'), ('Ablative Skin',
                    'Sabbat')] + [('Alexandra', 'CE'), ('Alexandra', None),
                ('Ablative Skin', None)] * 5
        aPhysCards = []
        for sName, sExp in aCards:
            oCard = self._gen_card(sName, sExp)
            aPhysCards.append(oCard)
        for oCard in aPhysCards:
            oPhysCardSet.addPhysicalCard(oCard.id)
            oPhysCardSet.syncUpdate()
        # Carry on with the test
        sConfigFile = self._create_tmp_file()
        oConfig = ConfigFile(sConfigFile)
        oWin = MultiPaneWindow()
        oWin.setup(oConfig)
        # Remove the unneeded panes
        oWin.remove_frame_by_name('Card Text')
        oWin.remove_frame_by_name('Card Set List')
        # Add one of the new card sets
        oWin.add_new_physical_card_set('Test Set 1')
        # Create selection of cards from the WW card list and
        # paste it into the new card set
        oFrame = oWin.find_pane_by_name('White Wolf Card List')
        self._select_cards(oFrame, [(u'AK-47', None),
            (u'AK-47', u'Lords of the Night')])
        self.assertEqual(oFrame.view.get_selection().count_selected_rows(), 2)
        # Copy
        oFrame.view.copy_selection()
        oNewFrame = oWin.find_pane_by_name('Test Set 1')
        oNewFrame.view.do_paste()
        self.assertEqual(len(oPCS2.cards), 2)
        # Check results
        # Select all and delete it from the new card set
        # Check results
        # Select card from My Collection and paste it into the card set
        # Check results
        # Select cards in new card set and change numbers
        # Check results
        # set editable off
        # Verify that trying to change the seleciton does nothing
        # set editable on and verify that we can change the numbers
        # rename card set, and verify that everything gets updated properly

if __name__ == "__main__":
    unittest.main()
