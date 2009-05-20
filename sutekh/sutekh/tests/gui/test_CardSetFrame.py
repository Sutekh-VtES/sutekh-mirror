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

    def test_basic(self):
        """Set of simple tests of the CardSetFrame"""
        # Skip if we're not under a windowing system
        # We need to do this before trying to run MultiPaneWindow's __init__,
        # which will fail if not under a windowing system
        if gtk.gdk.screen_get_default() is None:
            raise SkipTest
        # Add card sets needed for the tests
        oPhysCardSet = PhysicalCardSet(name='My Collection')
        PhysicalCardSet(name='Test Set 1',
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
