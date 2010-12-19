# test_FilterModelPanes.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test parts of the filter editor dialog"""

from sutekh.tests.GuiSutekhTest import GuiSutekhTest
import unittest
import gtk
from sutekh.core.FilterParser import FilterParser
from sutekh.gui.FilterModelPanes import FilterModelPanes
from sutekh.core.SutekhObjects import AbstractCard


class DummyDialog(gtk.Dialog):
    """Dumy dialog for the filter pane tests"""
    # pylint: disable-msg=R0904
    # gtk widget, so has many public methods

    def __init__(self):
        super(DummyDialog, self).__init__('Dummy', None, 0)
        # pylint: disable-msg=C0103
        # Needs to match the property name in the FilterDialog
        self.accel_group = gtk.AccelGroup()


class TestFilterModelPane(GuiSutekhTest):
    """Class for the FilterModelPanes tests"""

    def _check_asts(self, oAST1, oAST2):
        """Helper utility to check that two AST's generate identical
           results"""
        oFilter1 = oAST1.get_filter()
        oFilter2 = oAST2.get_filter()
        # We're not doing the PhysicalCard join, so select on abstract
        # card
        aResults1 = list(oFilter1.select(AbstractCard))
        aResults2 = list(oFilter2.select(AbstractCard))
        self.assertEqual(aResults1, aResults2, 'results differ: '
                '%s (from %s) != %s (from %s)' % (
                    aResults1, oAST1, aResults2, oAST2))

    def test_basic(self):
        """Set of simple tests of central part the Filter editor dialog"""
        # pylint: disable-msg=W0212
        # We directly access lots of internals details for testing
        # setup
        oParser = FilterParser()
        oDialog = DummyDialog()
        oFilterPanes = FilterModelPanes('PhysicalCard', oDialog)
        # check that we can round trip a filter with values
        oAST = oParser.apply('CardType in Equipment, Imbued or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes.replace_ast(oAST)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)
        # Check that we can disable parts of the filter (sect subfilter)
        oAST = oParser.apply('CardType in Equipment, Imbued or '
                'Discipline in Presence')

        # Check that we can re-enable bits

        # Check that we can negate bits
        oAST = oParser.apply('NOT CardType in Equipment, Imbued or '
                '(Discipline in Presence and Sect in Sabbat)')

        # Check that we can delete a value
        oAST = oParser.apply('CardType in Equipment or '
                '(Discipline in Presence and Sect in Sabbat)')

        # Check that a filter without values is disabled.
        oAST = oParser.apply('Discipline in Presence and Sect in Sabbat')

        # Check that we can delete a filter element with values
        oAST = oParser.apply('CardType in Equipment, Imbued or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes.replace_ast(oAST)
        oAST2 = oParser.apply('Discipline in Presence and Sect in Sabbat')

        # Check we can add filter values
        oAST = oParser.apply('CardType in Equipment or '
                '(Discipline in Presence and Sect in Sabbat)')

        # Check adding filter elements and filter values
        oAST = oParser.apply('CardType in Equipment or Keyword in location or '
                '(Discipline in Presence and Sect in Sabbat)')

    def test_widgets(self):
        """Test that various filters lead to the right type of widget"""
        # pylint: disable-msg=W0212
        # We directly access lots of internals details for testing
        oParser = FilterParser()
        oDialog = DummyDialog()
        oFilterPanes = FilterModelPanes('PhysicalCardSet', oDialog)
        # Check for none filter
        oAST = oParser.apply('CSSetsInUse')
        oFilterPanes.replace_ast(oAST)
        # Start with the filter box model selected
        # Label is the 2nd child
        oLabel = oFilterPanes._oSelectBar._oWidget.get_children()[1]
        self.assertEqual(oLabel.get_text(), "Or Drag Filter Element")
        # unselect
        oFilterPanes._oEditBox._oTreeView.get_selection().unselect_all()
        self.assertEqual(oFilterPanes._oSelectBar._oWidget,
                oFilterPanes._oSelectBar._oEmptyWidget)
        # select card set in use filter
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        self.assertEqual(oFilterPanes._oSelectBar._oWidget,
                oFilterPanes._oSelectBar._oNoneWidget)
        oAST = oParser.apply('CardSetAuthor in $x')
        oFilterPanes.replace_ast(oAST)
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        # check we have entry widget
        oEntry = oFilterPanes._oSelectBar._oWidget.get_children()[1]
        self.assertTrue(isinstance(oEntry, gtk.Entry))
        # change over to physical card filters
        oFilterPanes = FilterModelPanes('PhysicalCard', oDialog)
        oAST = oParser.apply('CardCount in $x')
        oFilterPanes.replace_ast(oAST)
        # check we have a count filter

        oAST = oParser.apply('Card_Sets in $x')
        oFilterPanes.replace_ast(oAST)
        # check we have a card set list filter

        oAST = oParser.apply('Discipline in $x')
        oFilterPanes.replace_ast(oAST)
        # check we have a values list filter


if __name__ == "__main__":
    unittest.main()
