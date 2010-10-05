# FilteredView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# Factored out from CardListView.py
# GPL - see COPYING for details

"""base classes for views."""

import gtk
import unicodedata
from sutekh.gui.CustomDragIconView import CustomDragIconView


class FilteredView(CustomDragIconView):
    """Base class for all card and card set views in Sutekh"""
    # pylint: disable-msg=R0904, R0902
    # gtk.Widget, so many public methods. We need to keep state, so many attrs

    def __init__(self, oController, oMainWindow, oModel, oConfig):
        # Although MainWindow usually contains a config_file property,
        # when we come in from the GuiCardLookup, we just have oConfig
        self._oController = oController
        self._oMainWin = oMainWindow
        self._oConfig = oConfig

        super(FilteredView, self).__init__(oModel)

        # subclasses will override this
        self._sDragPrefix = 'None:'

        # Filtering Dialog
        self._oFilterDialog = None

        # Text searching of card names
        self.set_search_equal_func(self.compare, None)

        self.set_name('filtered_view')

        # Enable rules hints
        self.set_rules_hint(True)

    # Introspection

    # pylint: disable-msg=W0212
    # We allow access via these properties (for plugins)
    mainwindow = property(fget=lambda self: self._oMainWin,
            doc="The parent window used for dialogs, etc.")
    controller = property(fget=lambda self: self._oController,
            doc="The controller used by the view.")
    frame = property(fget=lambda self: self._oController.frame,
            doc="The frame used by the view.")
    filterdialog = property(fget=lambda self: self._oFilterDialog,
            doc="The filter dialog.")
    # pylint: enable-msg=W0212

    def load(self):
        """Called when the model needs to be reloaded."""
        if hasattr(self._oMainWin, 'set_busy_cursor'):
            self._oMainWin.set_busy_cursor()
        self.freeze_child_notify()
        self.set_model(None)
        self._oModel.load()
        self.set_model(self._oModel)
        self.thaw_child_notify()
        if hasattr(self._oMainWin, 'restore_cursor'):
            self._oMainWin.restore_cursor()

    def reload_keep_expanded(self, bRestoreSelection=False):
        """Reload with current expanded state.

           Attempt to reload the card list, keeping the existing structure
           of expanded rows.
           """
        # Internal helper functions
        # See what's expanded
        sCurId = None
        aExpandedSet = self._get_expanded_list()
        if bRestoreSelection:
            aSelectedRows = self._get_selected_rows()
        oCurPath, _oCol = self.get_cursor()
        if oCurPath:
            sCurId = self.get_iter_identifier(
                    self._oModel.get_iter(oCurPath))
        # Reload, but use cached info
        self.load()
        # Re-expand stuff
        self._expand_list(aExpandedSet)
        if bRestoreSelection and aSelectedRows:
            self._reset_selected_rows(aSelectedRows)
        if oCurPath:
            # Restore cursor position if possible
            self._oModel.foreach(self._restore_cursor, sCurId)

    # Filtering

    # pylint: disable-msg=R0201
    # Method so sub-classes can override this

    def _get_filter_dialog(self, _sDefaultFilter):
        """Create the filter dialog if applicable for this view.

           The default doesn't create a dialog, but some subclasses
           do."""
        return False

    # pylint: enable-msg=R0201

    def get_filter(self, oMenu, sDefaultFilter=None):
        """Get the Filter from the FilterDialog.

           oMenu is a menu item to toggle if it exists.
           sDefaultFilterName is the name of the default filter
           to set when the dialog is created. This is intended for
           use by GuiCardLookup."""
        if self._oFilterDialog is None:
            if not self._get_filter_dialog(sDefaultFilter):
                return

        self._oFilterDialog.run()

        if self._oFilterDialog.was_cancelled():
            return  # Change nothing

        oFilter = self._oFilterDialog.get_filter()
        self.set_filter(oFilter, oMenu)

    def run_filter(self, bState):
        """Enable or disable the current filter based on bState"""
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self.reload_keep_expanded()

    # Helper function used by reload_keep_expanded

    def get_iter_identifier(self, oIter):
        """Get the identifier for the path.

           The identifier is (sTopLevel, sChildren, ...) as required."""
        aKey = []
        while oIter:
            aKey.append(self._oModel.get_value(oIter, 0))
            oIter = self._oModel.iter_parent(oIter)  # Move back up the model
        return ''.join(aKey)

    def _get_selected_rows(self):
        """Get the currently selected rows"""
        _oModel, aSelection = self._oSelection.get_selected_rows()
        aSelectedRows = set()
        for oPath in aSelection:
            aSelectedRows.add(self.get_iter_identifier(
                self._oModel.get_iter(oPath)))
        return aSelectedRows

    def _reset_selected_rows(self, aSelectedRows):
        """Reselect the rows"""
        self._oModel.foreach(self._set_row_selected_status, aSelectedRows)

    def _get_expanded_list(self):
        """Create a list of expanded rows"""
        aExpandedSet = set()
        self._oModel.foreach(self._get_row_expanded_status, aExpandedSet)
        return aExpandedSet

    def _expand_list(self, aExpandedSet):
        """Expand the rows listed in aExpandedSet"""
        self._oModel.foreach(self._set_row_expanded_status, aExpandedSet)

    @staticmethod
    def to_ascii(sName):
        """Convert a Name or key to a canonical ASCII form."""
        return unicodedata.normalize('NFKD', sName).encode('ascii', 'ignore')

    # pylint: disable-msg=R0913
    # Various arguments required by function signatures

    def _set_row_selected_status(self, _oModel, oPath, oIter, aSelectedSet):
        """Select the rows listed in aSelectedSet"""
        sKey = self.get_iter_identifier(oIter)
        if sKey in aSelectedSet:
            self._oSelection.select_path(oPath)
        return False

    def _restore_cursor(self, _oModel, oPath, oIter, sCursorId):
        """Select the rows listed in aSelectedSet"""
        sKey = self.get_iter_identifier(oIter)
        if sKey == sCursorId:
            self.set_cursor(oPath)
            # Ensure the cursor is visible
            self.scroll_to_cell(oPath, None, True, 0.5, 0.0)
        return False

    def _set_row_expanded_status(self, _oModel, oPath, oIter, aExpandedSet):
        """Attempt to expand the rows listed in aExpandedSet."""
        if not self._oModel.iter_has_child(oIter):
            # The tail nodes can't be expanded, only their parents,
            # so no need to check the tail nodes
            return False
        sKey = self.get_iter_identifier(oIter)
        if sKey in aExpandedSet:
            self.expand_to_path(oPath)
        return False

    def _get_row_expanded_status(self, _oModel, oPath, oIter, aExpandedSet):
        """Create a dictionary of rows and their expanded status."""
        if self.row_expanded(oPath):
            sKey = self.get_iter_identifier(oIter)
            aExpandedSet.add(sKey)
        return False  # Need to process the whole list

    # Name searching

    def compare(self, oModel, _iColumn, sKey, oIter, _oData):
        """Compare the entered text to the names."""

        def check_children(oModel, oIter, sKey, iLenKey):
            """expand children of this row that match."""
            oChildIter = oModel.iter_children(oIter)
            while oChildIter:
                sChildName = oModel.get_name_from_iter(oChildIter)
                sChildName = sChildName[:iLenKey].lower()
                if self.to_ascii(sChildName).startswith(sKey) or\
                    sChildName.startswith(sKey):
                    oPath = oModel.get_path(oChildIter)
                    # Expand the row
                    self.expand_to_path(oPath)
                if oModel.iter_n_children(oChildIter) > 0:
                    # recurse into the children
                    check_children(oModel, oChildIter, sKey, iLenKey)
                oChildIter = oModel.iter_next(oChildIter)

        sKey = sKey.lower()
        iLenKey = len(sKey)

        # Test this row straight up
        sCardSetName = self._oModel.get_name_from_iter(oIter)[:iLenKey].lower()
        if self.to_ascii(sCardSetName).startswith(sKey) or \
                sCardSetName.startswith(sKey):
            return False  # Match

        if oModel.iter_n_children(oIter) > 0:
            # row has children, so need to check if any of the children match
            check_children(oModel, oIter, sKey, iLenKey)
        # Fell through - the gtk continue search behaviour will find child
        # matches
        return True

    # helpers for selection management
    def set_select_none(self):
        """set selection to single mode"""
        self._oSelection.set_mode(gtk.SELECTION_NONE)

    def set_select_single(self):
        """set selection to single mode"""
        self._oSelection.set_mode(gtk.SELECTION_SINGLE)

    def set_select_multiple(self):
        """set selection to multiple mode"""
        self._oSelection.set_mode(gtk.SELECTION_MULTIPLE)

    def set_filter(self, oFilter, oMenu=None):
        """Set the current filter to oFilter & apply it."""
        if oFilter:
            self._oModel.selectfilter = oFilter
            if not self._oModel.applyfilter:
                # If a filter is set, automatically apply
                if oMenu:
                    oMenu.set_apply_filter(True)
                else:
                    self._oModel.applyfilter = True
            else:
                # Filter Changed, so reload
                self.reload_keep_expanded()
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if self._oModel.applyfilter:
                if oMenu:
                    oMenu.set_apply_filter(False)
                else:
                    self._oModel.applyfilter = False
            else:
                self.reload_keep_expanded()

    # drag-n-drop helpers
    # pylint: disable-msg=R0201
    # These need to be available to children as methods

    def split_selection_data(self, sSelectionData):
        """Helper function to subdivide selection string into bits again"""
        if sSelectionData == '':
            return 'None', ['']
        aLines = sSelectionData.splitlines()
        sSource = aLines[0]
        return sSource, aLines
