# CardSetManagementView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class the card sets."""

import gtk, gobject
import unicodedata
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.Filters import NullFilter

class CardSetManagementModel(gtk.TreeStore):
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    """TreeModel for the card sets"""
    def __init__(self, oMainWindow):
        super(CardSetManagementModel, self).__init__(gobject.TYPE_STRING)
        self._dName2Iter = {}

        self._oMainWin = oMainWindow

        self._bApplyFilter = False # whether to apply the select filter
        # additional filters for selecting from the list
        self._oSelectFilter = None
        self.oEmptyIter = None
        self.set_sort_func(0, self.sort_column)

    # pylint: disable-msg=W0212
    # W0212 - we explicitly allow access via these properties
    applyfilter = property(fget=lambda self: self._bApplyFilter,
            fset=lambda self, x: setattr(self, '_bApplyFilter', x))
    selectfilter = property(fget=lambda self: self._oSelectFilter,
            fset=lambda self, x: setattr(self, '_oSelectFilter', x))
    # pylint: enable-msg=W0212

    def get_card_set_iterator(self, oFilter):
        """Return an interator over the card set model.

           None may be used to retrieve the entire card set list
           """
        if not oFilter:
            oFilter = NullFilter()
        return oFilter.select(PhysicalCardSet).distinct()

    def load(self):
        """Load the card sets into the card view"""
        self.clear()
        oCardSetIter = self.get_card_set_iterator(self.get_current_filter())
        self._dName2Iter = {}

        # Loop through the card sets, getting the parent->child relationships
        for oCardSet in oCardSetIter:
            if oCardSet.parent:
                # Do funky stuff to make sure parent is shown in the view
                oParent = oCardSet
                aToAdd = []
                while oParent and oParent.name not in self._dName2Iter:
                    # FIXME: Add loop detection + raise error on loops
                    aToAdd.insert(0, oParent) # Insert at the head
                    oParent = oParent.parent
                if oParent and oParent.name in self._dName2Iter:
                    oIter = self._dName2Iter[oParent.name]
                else:
                    oIter = None
            else:
                # Just add
                oIter = None
                aToAdd = [oCardSet]
            for oSet in aToAdd:
                oIter = self.append(oIter)
                sName = oSet.name
                if self._oMainWin.find_pane_by_name(sName):
                    sName = '<i>%s</i>' % sName
                if oSet.inuse:
                    # In use sets are in bold
                    sName = '<b>%s</b>' % sName
                self.set(oIter, 0, sName)
                self._dName2Iter[oSet.name] = oIter

        if not self._dName2Iter:
            # Showing nothing
            self.oEmptyIter = self.append(None)
            sText = self._get_empty_text()
            self.set(self.oEmptyIter, 0, sText)

    def get_current_filter(self):
        """Get the current applied filter."""
        if self.applyfilter:
            return self.selectfilter
        else:
            return None

    def get_name_from_iter(self, oIter):
        """Extract the value at oIter from the model, correcting for encoding
           issues."""
        sCardSetName = self.get_value(oIter, 0).decode("utf-8")
        # Strip markup
        if sCardSetName.startswith('<b><i>'):
            sCardSetName = sCardSetName[6:-8]
        elif sCardSetName.startswith('<b>') or sCardSetName.startswith('<i>'):
            sCardSetName = sCardSetName[3:-4]
        return sCardSetName

    def get_name_from_path(self, oPath):
        """Get the card set name at oPath."""
        oIter = self.get_iter(oPath)
        return self.get_name_from_iter(oIter)

    def sort_column(self, oModel, oIter1, oIter2):
        """Custom sort function - ensure that markup doesn't affect sort
           order"""
        oCardSet1 = self.get_name_from_iter(oIter1)
        oCardSet2 = self.get_name_from_iter(oIter2)
        # get_name_from_iter strips markup for us
        return cmp(oCardSet1, oCardSet2)

    def _get_empty_text(self):
        """Get the correct text for an empty model."""
        if self.get_card_set_iterator(None).count() == 0:
            sText = 'Empty'
        else:
            sText = 'No Card Sets found'
        return sText


class CardSetManagementView(gtk.TreeView, object):
    """Tree View for the card sets."""
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

        self.connect('drag_data_get', self.drag_set)
        self.connect('drag_data_delete', self.drag_delete)
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

        oPath = oModel.get_path(oIter)
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

    # pylint: enable-msg=R0913, W0613

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
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self._oModel.load()

    def process_selection(self):
        """Create a dictionary from the selection."""
        pass

    def get_selection_as_string(self):
        """Get a string representing the current selection."""
        pass

    # Drag and Drop
    # Sub-classes should override as needed.
    # pylint: disable-msg=R0201
    # These need to be available to children as methods

    def drag_set(self, oBtn, oContext, oSelectionData, oInfo, oTime):
        """Create string representation of the selection for drag-n-drop"""
        pass

    def drag_delete(self, oBtn, oContext, oData):
        """Default drag-delete handler"""
        pass

    def get_selected_card_set(self):
        """Return the currently selected card set name, or None if nothing
           is selected."""
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        if len(aSelectedRows) < 1:
            return None
        # We only allow single selection mode, so len(aSelectedRows) == 1
        oPath = aSelectedRows[0]
        return oModel.get_name_from_path(oPath)

