# CardListView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView classes for displaying the card list."""

import gtk
import unicodedata
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.SearchDialog import SearchDialog

class CardListViewListener(object):
    """Listens to changes, i.e. .set_card_text(...) to CardListViews."""
    def set_card_text(self, oPhysCard):
        """The CardListView has called set_card_text on the CardText pane"""
        pass

class CardListView(gtk.TreeView):
    """Base class for all the card list views in Sutekh."""
    # pylint: disable-msg=R0904, R0902
    # gtk.Widget, so many public methods. We need to keep state, so many attrs
    def __init__(self, oController, oMainWindow, oModel, oConfig):
        # Although MainWindow usually contains a config_file property,
        # when we come in from the GuiCardLookup, we just have oConfig
        self._oModel = oModel
        self._oController = oController
        self._oMainWin = oMainWindow
        self._oConfig = oConfig
        # subclasses will override this
        self._sDragPrefix = 'None:'
        self.dListeners = {} # dictionary of CardListViewListeners

        super(CardListView, self).__init__(self._oModel)

        # Selecting rows
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_MULTIPLE)
        self._aOldSelection = []

        self._oSelection.connect('changed', self.card_selected)

        # Only enable icons if it's available (so we don't break GuiCardLookup)
        if hasattr(oMainWindow, 'icon_manager') and \
                hasattr(oModel, 'oIconManager'):
            oModel.oIconManager = oMainWindow.icon_manager

        self._oSelection.set_select_function(self.can_select)
        tGtkVersion = gtk.gtk_version
        if tGtkVersion[0] == 2 and \
                ((tGtkVersion[1] > 6 and tGtkVersion[1] < 12) or \
                (tGtkVersion[1] == 12 and tGtkVersion[2] == 0)):
            # gtk versions from 2.8 to 2.12.0 have a bug with handling
            # cursor movements, excluded selects and multiple select mode
            # ( http://bugzilla.gnome.org/show_bug.cgi?id=483730 )
            # We kludge around it via move_cursr
            self.connect('move-cursor', self.force_cursor_move)

        # Activating rows
        self.connect('row-activated', self.card_activated)
        # Key combination for searching

        # Text searching of card names
        self.set_search_equal_func(self.compare, None)
        # Search dialog
        # Entry item for text searching
        self._oSearchDialog = SearchDialog(self, self._oMainWin)

        # Drag and Drop
        aTargets = [ ('STRING', 0, 0),      # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here

        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                             aTargets,
                             gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                           aTargets,
                           gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get', self.drag_card)
        self.connect('drag_data_delete', self.drag_delete)
        self.connect('drag_data_received', self.card_drop)
        self.bReentrant = False
        self.bSelectTop = 0

        # Filtering Dialog
        self._oFilterDialog = None
        self.set_name('normal_view')

        # Grid Lines
        if hasattr(self, 'set_grid_lines'):
            self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)


    # Listener helper functions

    def add_listener(self, oListener):
        """Add a listener to the list."""
        self.dListeners[oListener] = None

    def remove_listener(self, oListener):
        """Remove a listener from the list."""
        del self.dListeners[oListener]

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

    def _set_row_status(self, _oModel, oPath, oIter, aExpandedSet):
        """Attempt to expand the rows listed in aExpandedSet."""
        if not self._oModel.iter_has_child(oIter):
            # The tail nodes can't be expanded, only their parents,
            # so no need to check the tail nodes
            return False
        sKey = self.get_iter_identifier(oIter)
        if sKey in aExpandedSet:
            self.expand_to_path(oPath)
        return False

    def get_iter_identifier(self, oIter):
        """Get the identifier for the path.

           The identifier is (sGroup, sCard, ...) as required."""
        aKey = []
        while oIter:
            aKey.append(self._oModel.get_value(oIter, 0))
            oIter = self._oModel.iter_parent(oIter) # Move back up the model
        return ''.join(aKey)

    def reload_keep_expanded(self):
        """Reload with current expanded state.

           Attempt to reload the card list, keeping the existing structure
           of expanded rows.
           """
        # Internal helper functions
        # See what's expanded
        aExpandedSet = self.get_expanded_list()
        # Reload, but use cached info
        self.load()
        # Re-expand stuff
        self.expand_list(aExpandedSet)

    def get_expanded_list(self):
        """Create a list of expanded rows"""
        aExpandedSet = set()
        self._oModel.foreach(self._get_row_status, aExpandedSet)
        return aExpandedSet

    def expand_list(self, aExpandedSet):
        """Expand the rows listed in aExpandedSet"""
        self._oModel.foreach(self._set_row_status, aExpandedSet)

    # Introspection

    # pylint: disable-msg=W0212
    # We allow access via these properties (for plugins)
    mainwindow = property(fget=lambda self: self._oMainWin,
            doc="The parent window used for dialogs, etc.")
    searchdialog = property(fget=lambda self: self._oSearchDialog,
            doc="The search dialog.")
    # pylint: enable-msg=W0212


    def can_select(self, oPath):
        """disable selecting top level rows"""
        if self.bSelectTop > 0:
            # Buggy gtk version work-around
            self.bSelectTop -= 1
            return True
        # In general, we don't allow the top level nodes to be selected
        return self._oModel.iter_parent(self._oModel.get_iter(oPath)) is \
                not None

    def card_selected(self, oSelection):
        """Change the selection behaviour.

           If we have multiple rows selected, and the user selects
           a single row that is in the selection, we DON'T change
           the selection, but we do update the card text and so on.
           """
        if self.bReentrant:
            # This is here because we alter the selection inside
            # this function (resulting in a nested call).
            # self.bReentrant is set and unset below.
            return False

        # If the selection is empty, clear everything and return
        if oSelection.count_selected_rows() <= 0:
            self._aOldSelection = []
            return False

        _oModel, aList = oSelection.get_selected_rows()
        # Implement the non default selection behaviour.
        tCursorPos = self.get_cursor()
        if len(aList) == 1 and len(self._aOldSelection) > 1 and \
            tCursorPos[0] == aList[0] and aList[0] in self._aOldSelection:
            # reset the list to it's previous state, but set
            # displayed card to this one
            try:
                self.bReentrant = True
                for oPath in self._aOldSelection:
                    oSelection.select_path(oPath)
            finally:
                self.bReentrant = False
            oPath = aList[0]
        else:
            _oModel, aList = oSelection.get_selected_rows()
            if not aList:
                self._aOldSelection = []
                return False

            if len(aList) <= len(self._aOldSelection):
                oPath = aList[-1]
            else:
                # Find the last entry in aList that's not in _aOldSelection
                oPath = [x for x in aList if x not in self._aOldSelection][-1]
            self._aOldSelection = aList

        oAbsCard = self._oModel.get_abstract_card_from_path(oPath)
        self._oController.set_card_text(oAbsCard)
        oPhysCard = self._oModel.get_physical_card_from_path(oPath)
        for oListener in self.dListeners:
            oListener.set_card_text(oPhysCard)

    # Filtering

    def get_filter(self, oMenu, sDefaultFilter=None):
        """Get the Filter from the FilterDialog.

           oMenu is a menu item to toggle if it exists.
           sDefaultFilterName is the name of the default filter
           to set when the dialog is created. This is intended for
           use by GuiCardLookup."""
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWin,
                    self._oConfig, self._oController.filtertype,
                    sDefaultFilter)

        self._oFilterDialog.run()

        if self._oFilterDialog.was_cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.get_filter()
        if oFilter != None:
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
                    self._oModel.applyfilter = True
            else:
                self.reload_keep_expanded()

    def run_filter(self, bState):
        """Enable or disable the current filter based on bState"""
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self.reload_keep_expanded()

    def process_selection(self):
        """Create a dictionary from the selection.

           Entries are of the form sCardName : {sExpansion1 : iCount1, ... }
           for use in drag-'n drop and elsewhere.
           """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            sCardName, sExpansion, iCount, iDepth = \
                    oModel.get_all_from_path(oPath)
            if iDepth == 0:
                # Skip top level items, since they're meaningless for the
                # selection
                continue
            # if a card is selected, then it's children (which are
            # the expansions) which are selected are ignored, since
            # We always treat this as all cards selected
            dSelectedData.setdefault(sCardName, {})
            if iDepth == 1:
                # Remove anything already assigned to this,
                # since parent overrides all
                dSelectedData[sCardName].clear()
                aChildren = oModel.get_child_entries_from_path(oPath)
                if len(aChildren) != 1:
                    # If there's more than 1 child, just go with unknown,
                    # as only sensible default
                    dSelectedData[sCardName]['None'] = iCount
                else:
                    # Otherwise, use the child, so filtering on
                    # physical expansion works as expected.
                    sExpansion, iCount = aChildren[0]
                    dSelectedData[sCardName][sExpansion] = iCount

            else:
                if 'None' in dSelectedData[sCardName]:
                    continue
                dSelectedData[sCardName][sExpansion] = iCount
        return dSelectedData

    def get_selection_as_string(self):
        """Get a string representing the current selection.

           Because of how pygtk handles drag-n-drop data, we need to
           create a string representating the card data."""
        if self._oSelection.count_selected_rows()<1:
            return ''
        dSelectedData = self.process_selection()
        # Create selection data structure
        # Need to bung everything into a string, alas
        sSelectData = self.sDragPrefix
        for sCardName in dSelectedData:
            for sExpansion, iCount in dSelectedData[sCardName].iteritems():
                sSelectData += '\n%(count)d\n%(name)s\n%(expansion)s' % {
                        'count' : iCount,
                        'name' : sCardName,
                        'expansion' : sExpansion,
                        }
        return sSelectData

    # Drag and Drop
    # Sub-classes should override as needed.
    # pylint: disable-msg=R0201
    # These need to be available to children as methods

    def split_selection_data(self, sSelectionData):
        """Helper function to subdivide selection string into bits again"""
        if sSelectionData == '':
            return 'None', ['']
        aLines = sSelectionData.splitlines()
        sSource = aLines[0]
        if sSource == "Sutekh Pane:" or sSource == 'Card Set:':
            return sSource, aLines
        # Construct list of (iCount, sCardName, sExpansion) tuples
        def true_expansion(sExpand):
            """Convert back from the 'None' placeholder in the string"""
            # The logic goes that, if the user has dragged the top level cards,
            # Then either all the cards are going to be copied, or there is
            # no expansion info, so the expansion might as well be none.
            if sExpand == 'None':
                return None
            else:
                return sExpand
        aCardInfo = zip([int(x) for x in aLines[1::3]], aLines[2::3],
                [true_expansion(x) for x in aLines[3::3]])
        return sSource, aCardInfo

    # pylint: disable-msg=R0913
    # arguments as required by the function signature

    def drag_card(self, oBtn, oContext, oSelectionData, oInfo, oTime):
        """Create string representation of the selection for drag-n-drop"""
        sSelectData = self.get_selection_as_string()
        if sSelectData == '':
            # Pass over to the frame handler
            self._oController.frame.create_drag_data(oBtn, oContext,
                    oSelectionData, oInfo, oTime)
            return
        oSelectionData.set(oSelectionData.target, 8, sSelectData)

    def drag_delete(self, oBtn, oContext, oData):
        """Default drag-delete handler"""
        pass

    def card_drop(self, oWdgt, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Default drag-n-drop handler."""
        # Pass off to the Frame Handler
        self._oController.frame.drag_drop_handler(oWdgt, oContext, iXPos,
                iYPos, oData, oInfo, oTime)

    def copy_selection(self):
        """Copy the current selection to the application clipboard"""
        sSelection = self.get_selection_as_string()
        self._oMainWin.set_selection_text(sSelection)

    # Card name searching

    @staticmethod
    def to_ascii(sName):
        """Convert a card name or key to a canonical ASCII form."""
        return unicodedata.normalize('NFKD', sName).encode('ascii','ignore')

    def compare(self, oModel, _iColumn, sKey, oIter, _oData):
        """Compare the entered text to the card names."""
        if oModel.iter_depth(oIter) == 2:
            # Don't succeed for expansion items
            return True

        oPath = oModel.get_path(oIter)
        sKey = sKey.lower()
        iLenKey = len(sKey)

        if oModel.iter_depth(oIter) == 0:
            if self.row_expanded(oPath):
                # Don't succeed for expanded top level items
                return True
            else:
                # Need to check if any of the children match
                oChildIter = self._oModel.iter_children(oIter)
                while oChildIter:
                    sChildName = self._oModel.get_name_from_iter(oChildIter)
                    sChildName = sChildName[:iLenKey].lower()
                    if self.to_ascii(sChildName).startswith(sKey) or\
                        sChildName.startswith(sKey):
                        # Expand the row
                        self.expand_to_path(oPath)
                        # Bail out, as compare will find the match for us
                        return True
                    oChildIter = self._oModel.iter_next(oChildIter)
                return True # No matches, so bail

        sCardName = self._oModel.get_name_from_iter(oIter)[:iLenKey].lower()
        if self.to_ascii(sCardName).startswith(sKey) or \
                sCardName.startswith(sKey):
            return False

        return True

    # pylint: enable-msg=R0913

    # Helper function used by reload_keep_expanded
    # Various arguments required by function signatures
    def _get_row_status(self, _oModel, oPath, oIter, aExpandedSet):
        """Create a dictionary of rows and their expanded status."""
        if self.row_expanded(oPath):
            sKey = self.get_iter_identifier(oIter)
            aExpandedSet.add(sKey)
        return False # Need to process the whole list

    # Activating Rows
    def card_activated(self, _oTree, oPath, _oColumn):
        """Update card text and notify listeners when a card is selected."""
        oAbsCard = self._oModel.get_abstract_card_from_path(oPath)
        oPhysCard = self._oModel.get_physical_card_from_path(oPath)
        self._oController.set_card_text(oAbsCard)
        for oListener in self.dListeners:
            oListener.set_card_text(oPhysCard)

    # Selecting

    def force_cursor_move(self, _oTreeView, _iStep, _iCount):
        """Special handling for move events for buggy gtk events.

           We need to allow the selection of top level items when
           moving the cursor over them
           """
        oCurPath, _oColumn = self.get_cursor()
        if self._oModel.iter_parent(self._oModel.get_iter(oCurPath)) is None:
            # Root node, so need to force the move
            self.bSelectTop = 2
            # Need to succeed twice - once to select, once to unselect
            # I don't quite understand why this works this way, but it
            # does
            self._oSelection.select_path(oCurPath)
        # Let gtk handle the rest of the move, since we're not doing
        # anything else funky
        return False

