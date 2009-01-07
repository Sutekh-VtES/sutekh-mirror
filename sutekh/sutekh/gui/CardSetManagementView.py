# CardSetManagementView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class the card set list."""

import gtk
import unicodedata
from sutekh.gui.CardSetManagementModel import CardSetManagementModel
from sutekh.gui.SearchDialog import SearchDialog

class CardSetManagementView(gtk.TreeView, object):
    """Tree View for the card set list."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    def __init__(self, oMainWindow, oController):
        self._oModel = CardSetManagementModel(oMainWindow)
        super(CardSetManagementView, self).__init__(self._oModel)

        self._oMainWin = oMainWindow
        self._oController = oController

        # Selecting rows
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_SINGLE)

        # Text searching of card names
        self.set_search_equal_func(self.compare, None)
        # Search dialog
        # Entry item for text searching
        self._oSearchDialog = SearchDialog(self, self._oMainWin)

        # Drag and Drop
        aTargets = [ ('STRING', 0, 0),      # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here

        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get', self.drag_card_set)
        self.connect('row_activated', self._oController.row_clicked)
        self.connect('drag_data_received', self._oController.card_set_drop)

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
    def get_row_status(self, oModel, oPath, oIter, dExpandedDict):
        """Create a dictionary of rows and their expanded status."""
        if self.row_expanded(oPath):
            dExpandedDict.setdefault(oPath,
                    self._oModel.get_name_from_path(oPath))
        return False # Need to process the whole list

    # pylint: disable-msg=W0613

    def set_row_status(self, dExpandedDict):
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

    # Introspection

    # pylint: disable-msg=W0212
    # We allow access via these properties (for plugins)
    mainwindow = property(fget=lambda self: self._oMainWin,
            doc="The parent window sed for dialogs, etc.")
    searchdialog = property(fget=lambda self: self._oSearchDialog,
            doc="The search dialog.")
    # pylint: enable-msg=W0212

    # Card Set Name searching

    @staticmethod
    def to_ascii(sName):
        """Convert a card name or key to a canonical ASCII form."""
        return unicodedata.normalize('NFKD', sName).encode('ascii','ignore')

    # pylint: disable-msg=R0913, W0613
    # arguments as required by the function signature
    def compare(self, oModel, iColumn, sKey, oIter, oData):
        """Compare the entered text to the card names."""

        def check_children(oModel, oIter, sKey, iLenKey):
            """Check if the children of this iterator match."""
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

    def get_path_at_pointer(self):
        """Get the path at the current pointer position"""
        # pylint: disable-msg=W0612
        # we ignore oIgnore
        iXPos, iYPos, oIgnore = self.get_bin_window().get_pointer()
        tRes = self.get_path_at_pos(iXPos, iYPos)
        if tRes:
            return tRes[0]
        return None
