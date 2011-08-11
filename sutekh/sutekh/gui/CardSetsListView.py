# CardSetsListView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class for the card set list."""

import gtk
from sutekh.gui.CardSetManagementModel import CardSetManagementModel
from sutekh.gui.FilteredView import FilteredView


class CardSetsListView(FilteredView):
    """Tree View for the card set list."""
    # pylint: disable-msg=R0904, R0902, R0901
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We need to track a fair amount of state, so many attributes
    # R0901 - many ancestors, due to our object hierachy on top of the quite
    # deep gtk one
    def __init__(self, oController, oMainWindow, bSpecialSelect=False):
        oModel = CardSetManagementModel(oMainWindow)
        oModel.enable_sorting()
        if hasattr(oMainWindow, 'config_file'):
            oConfig = oMainWindow.config_file
        else:
            oConfig = None
        super(CardSetsListView, self).__init__(oController, oMainWindow,
                oModel, oConfig)

        self.set_name('card set list view')

        self.oNameCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Card Sets", self.oNameCell, markup=0)
        oColumn.set_expand(True)
        oColumn.set_resizable(True)
        oColumn.set_sort_column_id(0)
        self.append_column(oColumn)
        self._oModel.load()

        self.set_expander_column(oColumn)

        self._oSelection.set_select_function(self.can_select)

        if bSpecialSelect:
            self._oSelection.connect('changed', self.row_selected)

    def can_select(self, oPath):
        """disable selecting of excluded items"""
        sName = self._oModel.get_name_from_path(oPath)
        return not self._oModel.is_excluded(sName)

    def exclude_set(self, sSetName):
        """Mark a set as excluded"""
        self._oModel.exclude_set(sSetName)

    def get_selected_card_set(self):
        """Return the currently selected card set name, or None if nothing
           is selected."""
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        if len(aSelectedRows) != 1:
            # Only viable when a single row is selected
            return None
        oPath = aSelectedRows[0]
        return oModel.get_name_from_path(oPath)

    def _select_set(self, sCardSetName):
        """Add the specified set to the selection"""
        aIters = [self._oModel.get_iter_first()]
        while aIters:
            oIter = aIters.pop()
            while oIter is not None:
                if sCardSetName == self._oModel.get_name_from_iter(oIter):
                    oPath = self._oModel.get_path(oIter)
                    self.expand_to_path(oPath)
                    self._oSelection.select_iter(oIter)
                    return  # No need to continue
                if self._oModel.iter_has_child(oIter):
                    aIters.append(self._oModel.iter_children(oIter))
                oIter = self._oModel.iter_next(oIter)

    def set_selected_card_set(self, sCardSetName):
        """Set the currently selected card set."""
        self._oSelection.unselect_all()
        self._select_set(sCardSetName)

    def set_all_selected_sets(self, aSetNames):
        """Set all the sets"""
        self._oSelection.unselect_all()
        for sCardSetName in aSetNames:
            self._select_set(sCardSetName)

    def get_all_selected_sets(self):
        """Return a list of all the selected sets"""
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        if len(aSelectedRows) < 1:
            return None
        aSets = []
        for oPath in aSelectedRows:
            aSets.append(oModel.get_name_from_path(oPath))
        return aSets

    def get_selection_object(self):
        """Return the selection object for this list"""
        return self._oSelection

    def _check_row_for_entry(self, _oModel, oPath, oIter, sEntry):
        """Check if row matches the entry, and expand it if so"""
        sRow = self._oModel.get_name_from_iter(oIter)
        if sRow == sEntry:
            self.expand_to_path(oPath)

    def expand_to_entry(self, sEntry):
        """Find the entry with the text sEntry, and expand the appropriate
           row."""
        self._oModel.foreach(self._check_row_for_entry, sEntry)
