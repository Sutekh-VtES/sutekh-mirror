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
from sutekh.gui.FilterModelPanes import FilterModelPanes, \
        FilterEditorToolbar, ENTER_KEYS
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.core.SutekhObjects import AbstractCard


class DummyDialog(gtk.Dialog):
    """Dummy dialog for the filter pane tests"""
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
        # pylint: disable-msg=W0212, R0915
        # W0212: We directly access lots of internals details for testing
        # setup
        # R0915: Long test case to avoid repeated setups
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
        oAST2 = oParser.apply('CardType in Equipment, Imbued or '
                'Discipline in Presence')
        # select sect
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:1:1')
        oFilterPanes._oSelectBar._oBoxModelEditor.set_disabled(True)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST2, oFilterAST)
        # Check that we can re-enable bits
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:1:1')
        oFilterPanes._oSelectBar._oBoxModelEditor.set_disabled(False)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)

        # Check that we can negate bits
        oAST = oParser.apply('NOT CardType in Equipment, Imbued or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        oFilterPanes._oSelectBar._oBoxModelEditor.set_negate(True)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)
        # reset
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        oFilterPanes._oSelectBar._oBoxModelEditor.set_negate(False)

        # Check that we can delete a value
        oAST = oParser.apply('CardType in Equipment or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0:1')
        oFilterPanes._oEditBox._oTreeView.set_cursor('0:0:1')
        oFilterPanes._oSelectBar._oBoxModelEditor.delete(None)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)

        # Check that a filter without values is disabled.
        oAST = oParser.apply('Discipline in Presence and Sect in Sabbat')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0:0')
        oFilterPanes._oEditBox._oTreeView.set_cursor('0:0:0')
        oFilterPanes._oSelectBar._oBoxModelEditor.delete(None)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)

        # Check we can add filter values
        oAST = oParser.apply('CardType in Equipment or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        oFilterPanes._oEditBox._oTreeView.set_cursor('0:0')
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[0]
        # check we can round trip setting a discipline on the list
        oList = oWidget.get_child()
        oList.set_selected_entry('Equipment')
        oFilter = oFilterPanes._oSelectBar._oLastFilter
        oEvent = gtk.gdk.Event(gtk.gdk.KEY_PRESS)
        # ENTER_KEYS contains longs, but keyval needs int
        oEvent.keyval = int(list(ENTER_KEYS)[0])
        oEvent.state = gtk.gdk.CONTROL_MASK
        oFilterPanes._oSelectBar.key_press(oFilterPanes._oSelectBar._oWidget,
                oEvent, oFilter, 'Value')
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)

        # Check that we can delete a filter element with values
        oAST = oParser.apply('Discipline in Presence and Sect in Sabbat')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        oFilterPanes._oEditBox._oTreeView.set_cursor('0:0')
        oFilterPanes._oSelectBar._oBoxModelEditor.delete(None)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)

        # Check adding filter elements and filter values
        oAST = oParser.apply('CardType in Equipment or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes.replace_ast(oAST)
        oAST = oParser.apply('CardType in Equipment or Keyword in location or '
                '(Discipline in Presence and Sect in Sabbat)')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0')
        oFilterPanes._oEditBox._oTreeView.set_cursor('0')
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[2]
        # check we can round trip setting a discipline on the list
        oToolbar = oWidget.get_child()
        oListStore = oToolbar._oListStore
        oSelection = oToolbar.get_selection()
        oIter = oListStore.get_iter_root()
        while oIter:
            if oListStore.get_value(oIter, 0) == 'Keyword':
                oSelection.select_path(oListStore.get_path(oIter))
                break
            oIter = oListStore.iter_next(oIter)
        oFilter = oFilterPanes._oSelectBar._oLastFilter
        # ENTER_KEYS contains longs, but keyval needs int
        oFilterPanes._oSelectBar.key_press(oToolbar, oEvent, oFilter, 'Filter')
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:2')
        oFilterPanes._oEditBox._oTreeView.set_cursor('0:2')
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[0]
        # check we can round trip setting a discipline on the list
        oList = oWidget.get_child()
        oList.set_selected_entry('location')
        oFilter = oFilterPanes._oSelectBar._oLastFilter
        oFilterPanes._oSelectBar.key_press(oFilterPanes._oSelectBar._oWidget,
                oEvent, oFilter, 'Value')
        # ENTER_KEYS contains longs, but keyval needs int
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oAST, oFilterAST)

    def test_quoting(self):
        """Test that quotes are properly escaped from the gui widget"""
        # pylint: disable-msg=W0212, R0915
        # W0212: We directly access lots of internals details for testing
        # setup
        # R0915: Long test case to avoid repeated setups
        oParser = FilterParser()
        oDialog = DummyDialog()
        oFilterPanes = FilterModelPanes('PhysicalCard', oDialog)
        oAST = oParser.apply('CardName in $x')
        oFilterPanes.replace_ast(oAST)
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        # check we have entry widget
        oEntry = oFilterPanes._oSelectBar._oWidget.get_children()[1]

        oEntry.set_text('"')
        oFilterAST = oFilterPanes.get_ast_with_values()
        oDoubleQuoteAST = oParser.apply('CardName in \'"\'')
        self._check_asts(oDoubleQuoteAST, oFilterAST)

        oEntry.set_text("'")
        oFilterAST = oFilterPanes.get_ast_with_values()
        oSingleQuoteAST = oParser.apply('CardName in "\'"')
        self._check_asts(oSingleQuoteAST, oFilterAST)

        # Check quotes round trip properly
        oFilterPanes.replace_ast(oSingleQuoteAST)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oSingleQuoteAST, oFilterAST)
        oFilterPanes.replace_ast(oDoubleQuoteAST)
        oFilterAST = oFilterPanes.get_ast_with_values()
        self._check_asts(oDoubleQuoteAST, oFilterAST)

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
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[2]
        self.assertTrue(isinstance(oWidget.get_child(), FilterEditorToolbar))
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
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        # check we have a count filter
        oLabel = oFilterPanes._oSelectBar._oWidget.get_children()[1]
        self.assertEqual(oLabel.get_text(), "From")
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[2]
        self.assertTrue(isinstance(oWidget.get_child(), CardSetsListView))

        oAST = oParser.apply('Card_Sets in $x')
        oFilterPanes.replace_ast(oAST)
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        # check we have a card set list filter
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[0]
        self.assertTrue(isinstance(oWidget, CardSetsListView))

        oAST = oParser.apply('Discipline in $x')
        oFilterPanes.replace_ast(oAST)
        oFilterPanes._oEditBox._oTreeView.get_selection().select_path('0:0')
        # check we have a values list filter
        oWidget = oFilterPanes._oSelectBar._oWidget.get_children()[0]
        self.assertTrue(isinstance(oWidget, AutoScrolledWindow))
        # check we can round trip setting a discipline on the list
        oList = oWidget.get_child()
        oList.set_selected_entry('Presence')
        self.assertEqual(oList.get_selected_data(), ['Presence'])


if __name__ == "__main__":
    unittest.main()
