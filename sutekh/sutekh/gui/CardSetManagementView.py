# CardSetManagementView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class the card set list."""

import gtk
import unicodedata
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.CardSetManagementModel import CardSetManagementModel

class CardSetManagementView(gtk.TreeView, object):
    """Tree View for the card set list."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    def __init__(self, oMainWindow):
        self._oModel = CardSetManagementModel(oMainWindow)
        super(CardSetManagementView, self).__init__(self._oModel)

        self._oMainWin = oMainWindow

        # Selecting rows
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_SINGLE)

        # Text searching of card names
        self.set_search_equal_func(self.compare, None)
        self.set_enable_search(True)

        # Drag and Drop
        aTargets = [ ('STRING', 0, 0),      # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here

        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get', self.drag_card_set)
        self.connect('row_activated', self.row_clicked)
        self.bReentrant = False
        self.bSelectTop = 0

        # Filtering Dialog
        self._oFilterDialog = None
        self.set_name('card set view')

        # Grid Lines
        if hasattr(self, 'set_grid_lines'):
            self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)

        self.oNameCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Card Sets", self.oNameCell, markup=0)
        oColumn.set_expand(True)
        oColumn.set_sort_column_id(0)
        self.append_column(oColumn)
        self._oModel.load()

    # Help functions used by reload_keep_expanded
    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def __get_row_status(self, oModel, oPath, oIter, dExpandedDict):
        """Create a dictionary of rows and their expanded status."""
        if self.row_expanded(oPath):
            dExpandedDict.setdefault(oPath,
                    self._oModel.get_name_from_path(oPath))
        return False # Need to process the whole list

    # pylint: disable-msg=W0613

    def __set_row_status(self, dExpandedDict):
        """Attempt to expand the rows listed in dExpandedDict."""
        for oPath in dExpandedDict:
            # pylint: disable-msg=W0704
            # Paths may disappear, so this error can be ignored
            try:
                sCardSetName = self._oModel.get_name_from_path(oPath)
                if sCardSetName == dExpandedDict[oPath]:
                    self.expand_to_path(oPath)
            except ValueError:
                pass
        return False

    def reload_keep_expanded(self, bRestoreSelection):
        """Reload with current expanded state.

           Attempt to reload the card list, keeping the existing structure
           of expanded rows.
           """
        # Internal helper functions
        # See what's expanded
        # pylint: disable-msg=W0612
        # we're not interested in oModel here
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        if len(aSelectedRows) > 0:
            oSelPath = aSelectedRows[0]
        else:
            oSelPath = None
        dExpandedDict = {}
        self._oModel.foreach(self.__get_row_status, dExpandedDict)
        # Reload, but use cached info
        self._oModel.load()
        # Re-expand stuff
        self.__set_row_status(dExpandedDict)
        if oSelPath and bRestoreSelection:
            # Restore selection
            self._oSelection.select_path(oSelPath)

    # Introspection

    # pylint: disable-msg=W0212
    # We allow access via these properties (for plugins)
    mainwindow = property(fget=lambda self: self._oMainWin,
            doc="The parent window sed for dialogs, etc.")
    # pylint: enable-msg=W0212

    # Card Set Name searching

    @staticmethod
    def to_ascii(sName):
        """Convert a card name or key to a canonical ASCII form."""
        return unicodedata.normalize('NFKD', sName).encode('ascii','ignore')

    # Filtering

    def get_filter(self, oMenu):
        """Get the Filter from the FilterDialog."""
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWin,
                    self._oMainWin.config_file, 'PhysicalCardSet')

        self._oFilterDialog.run()

        if self._oFilterDialog.was_cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.get_filter()
        if oFilter != None:
            # pylint: disable-msg=C0103
            # selectfilter OK here
            self._oModel.selectfilter = oFilter
            if not self._oModel.applyfilter:
                # If a filter is set, automatically apply
                oMenu.set_apply_filter(True)
            else:
                # Filter Changed, so reload
                self._oModel.load()
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if self._oModel.applyfilter:
                oMenu.set_apply_filter(False)
            else:
                self._oModel.load()

    def run_filter(self, bState):
        """Enable or diable the current filter based on bState"""
        # pylint: disable-msg=C0103
        # applyfilter OK here
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self._oModel.load()

    # pylint: disable-msg=R0913, W0613
    # arguments as required by the function signature
    def compare(self, oModel, iColumn, sKey, oIter, oData):
        """Compare the entered text to the card names."""

        def check_children(oModel, oIter, sKey, iLenKey):
            """Check if the children of this iterator match."""
            for iChildCount in range(oModel.iter_n_children(oIter)):
                oChildIter = oModel.iter_nth_child(oIter, iChildCount)
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

        sKey = sKey.lower()
        iLenKey = len(sKey)

        # Test this row straight up
        sCardSetName = self._oModel.get_name_from_iter(oIter)[:iLenKey].lower()
        if self.to_ascii(sCardSetName).startswith(sKey) or \
                sCardSetName.startswith(sKey):
            return False

        if oModel.iter_n_children(oIter) > 0:
            # row has children, so need to check if any of the children match
            check_children(oModel, oIter, sKey, iLenKey)
        # Fell through
        return True


    def drag_card_set(self, oBtn, oDragContext, oSelectionData, oInfo, oTime):
        """Allow card sets to be dragged to a frame."""
        sSetName = self.get_selected_card_set()
        if not sSetName:
            return
        sData = "\n".join(['Card Set:', sSetName])
        oSelectionData.set(oSelectionData.target, 8, sData)

    def row_clicked(self, oTreeView, oPath, oColumn):
        """Handle row clicked events.

           allow double clicks to open a card set.
           """
        oModel = self.get_model()
        sName = oModel.get_name_from_path(oPath)
        # check if card set is open before opening again
        oPane = self._oMainWin.find_pane_by_name(sName)
        if oPane is not None:
            return # Already open, so do nothing
        self._oMainWin.add_new_physical_card_set(sName)

    # pylint: enable-msg=R0913, W0613

    def get_selected_card_set(self):
        """Return the currently selected card set name, or None if nothing
           is selected."""
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        if len(aSelectedRows) < 1:
            return None
        # We only allow single selection mode, so len(aSelectedRows) == 1
        oPath = aSelectedRows[0]
        return oModel.get_name_from_path(oPath)

