# CardListView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView classes for displaying the card list."""

import gtk, pango
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton

class CardListViewListener(object):
    """Listens to changes, i.e. .set_card_text(...) to CardListViews."""
    def set_card_text(self, sCardName, sExpansion):
        """The CardListViw has called set_card_text on the CardText pane"""
        pass

class CardListView(gtk.TreeView, object):
    """Base class for all the card list views in Sutekh."""
    # pylint: disable-msg=R0904, R0902
    # gtk.Widget, so many public methods. We need to keep state, so many attrs
    def __init__(self, oController, oMainWindow, oModel):
        self._oModel = oModel
        self._oController = oController
        self._oMainWin = oMainWindow
        self._oConfig = oMainWindow.config_file
        self.dListeners = {} # dictionary of CardListViewListeners

        super(CardListView, self).__init__(self._oModel)

        # Selecting rows
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_MULTIPLE)
        self._aOldSelection = []

        self._oSelection.connect('changed', self.card_selected)

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
        # Key combination for expanding and collapsing all rows
        self.connect('key-release-event', self.key_released)

        # Text searching of card names
        self.set_search_equal_func(self.compare, None)
        self.set_enable_search(True)

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
        self._oModel.load()

    # Help functions used by reload_keep_expanded
    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def __get_row_status(self, oModel, oPath, oIter, dExpandedDict):
        """Create a dictionary of rows and their expanded status."""
        if self.row_expanded(oPath):
            dExpandedDict.setdefault(oPath,
                    self._oModel.get_card_name_from_path(oPath))
        return False # Need to process the whole list

    # pylint: disable-msg=W0613

    def __set_row_status(self, dExpandedDict):
        """Attempt to expand the rows listed in dExpandedDict."""
        for oPath in dExpandedDict:
            # pylint: disable-msg=W0704
            # Paths may disappear, so this error can be ignored
            try:
                sCardName = self._oModel.get_card_name_from_path(oPath)
                if sCardName == dExpandedDict[oPath]:
                    self.expand_to_path(oPath)
            except ValueError:
                pass
        return False

    def reload_keep_expanded(self):
        """Reload with current expanded state.

           Attempt to reload the card list, keeping the existing structure
           of expanded rows.
           """
        # Internal helper functions
        # See what's expanded
        dExpandedDict = {}
        self._oModel.foreach(self.__get_row_status, dExpandedDict)
        # Reload, but use cached info
        self.load()
        # Re-expand stuff
        self.__set_row_status(dExpandedDict)

    # Introspection

    # pylint: disable-msg=W0212
    # We allow access via these properties (for plugins)
    window = property(fget=lambda self: self._oMainWin,
            doc="The parent window sed for dialogs, etc.")
    # pylint: enable-msg=W0212

    # Activating Rows

    # pylint: disable-msg=W0613
    # Various arguments required by function signatures
    def card_activated(self, oTree, oPath, oColumn):
        """Update card text and notify listeners when a card is selected."""
        sCardName = self._oModel.get_card_name_from_path(oPath)
        self._oController.set_card_text(sCardName)
        for oListener in self.dListeners:
            oListener.set_card_text(sCardName, '')

    # Key combinations

    def key_released(self, oWidget, oEvent):
        """Hook into the key processsing loop to do interesting things."""
        oCtrlAlt = (gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK)
        # We ignore shift, since we need it for Ctrl+ and such
        if oEvent.get_state() & oCtrlAlt == \
                gtk.gdk.CONTROL_MASK:
            # control key was pressed
            if oEvent.keyval == gtk.gdk.keyval_from_name('plus'):
                self.expand_all()
                return True
            elif oEvent.keyval == gtk.gdk.keyval_from_name('minus'):
                self.collapse_all()
                return True
            elif gtk.gdk.keyval_to_lower(oEvent.keyval) == \
                    gtk.gdk.keyval_from_name('c'):
                sSelection = self.get_selection_as_string()
                self._oMainWin.set_selection_text(sSelection)
            elif gtk.gdk.keyval_to_lower(oEvent.keyval) == \
                    gtk.gdk.keyval_from_name('v'):
                if self._oModel.bEditable:
                    sSelection = self._oMainWin.get_selection_text()
                    sSource, aCards = self.split_selection_data(sSelection)
                    if sSource != self.sDragPrefix:
                        # Prevent pasting into oneself
                        self.add_paste_data(sSource, aCards)
        elif oEvent.get_state() & oCtrlAlt == 0:
            # No modifiers of interest pressed
            if oEvent.keyval == gtk.gdk.keyval_from_name('Delete'):
                self.del_selection()
        # Let other key handles take charge
        return False


    # Selecting

    def force_cursor_move(self, oTreeView, iStep, iCount):
        """Special handling for move events for buggy gtk events.

           We need to allow the selection of top level items when
           moving the cursor over them
           """
        # pylint: disable-msg=W0612
        # We're only interested in oCurPath
        (oCurPath, oColumn) = self.get_cursor()
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

    # pylint: enable-msg=W0613

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

        # pylint: disable-msg=W0612
        # We're only interested in aList
        oModel, aList = oSelection.get_selected_rows()
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
            oModel, aList = oSelection.get_selected_rows()
            if not aList:
                self._aOldSelection = []
                return False

            if len(aList) <= len(self._aOldSelection):
                oPath = aList[-1]
            else:
                # Find the last entry in aList that's not in _aOldSelection
                oPath = [x for x in aList if x not in self._aOldSelection][-1]
            self._aOldSelection = aList

        sCardName = self._oModel.get_card_name_from_path(oPath)
        self._oController.set_card_text(sCardName)
        sExpansion = self._oModel.get_exp_name_from_path(oPath)
        if not sExpansion:
            sExpansion = ''
        for oListener in self.dListeners:
            oListener.set_card_text(sCardName, sExpansion)

    # Card name searching

    # pylint: disable-msg=R0913, W0613
    # arguments as required by the function signature
    def compare(self, oModel, iColumn, sKey, oIter, oData):
        """Compare the entered text to the card names."""
        if oModel.iter_depth(oIter) == 2:
            # Don't succeed for expansion items
            return True

        oPath = oModel.get_path(oIter)

        if oModel.iter_depth(oIter) == 0:
            if self.row_expanded(oPath):
                # Don't succeed for expanded top level items
                return True
            else:
                # Need to check if any of the children match
                for iChildCount in range(oModel.iter_n_children(oIter)):
                    oChildIter = oModel.iter_nth_child(oIter, iChildCount)
                    sChildName = self._oModel.get_name_from_iter(
                            oChildIter).lower()
                    if sChildName.startswith(sKey.lower()):
                        # Expand the row
                        self.expand_to_path(oPath)
                        # Bail out, as compare will find the match for us
                        return True
                return True # No matches, so bail

        sCardName = self._oModel.get_name_from_iter(oIter).lower()
        if sCardName.startswith(sKey.lower()):
            return False

        return True

    # pylint: enable-msg=R0913, W0613

    # Filtering

    def get_filter(self, oMenu):
        """Get the Filter from the FilterDialog."""
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWin,
                    self._oConfig, self._oController.filtertype)

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
                self.load()
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if self._oModel.applyfilter:
                oMenu.set_apply_filter(False)
            else:
                self.load()

    def run_filter(self, bState):
        """Enable or diable the current filter based on bState"""
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self.load()

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
                dSelectedData[sCardName]['None'] = iCount
            else:
                if 'None' in dSelectedData[sCardName]:
                    continue
                dSelectedData[sCardName][sExpansion] = iCount
        return dSelectedData

    def get_selection_as_string(self):
        """Get a string representing the current selection."""
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

    def del_selection(self):
        """try to delete all the cards in the current selection"""
        if self._oModel.bEditable:
            dSelectedData = self.process_selection()
            for sCardName in dSelectedData:
                for sExpansion, iCount in dSelectedData[sCardName].iteritems():
                    # pylint: disable-msg=W0612
                    # iAttempt is loop counter
                    for iAttempt in range(iCount):
                        if sExpansion != 'None':
                            self._oController.dec_card(sCardName, sExpansion)
                        else:
                            self._oController.dec_card(sCardName, None)

    # Drag and Drop
    # Sub-classes should override as needed.
    # pylint: disable-msg=R0201
    # These need to be available to children as methods

    def drag_card(self, oBtn, oContext, oSelection_data, oInfo, oTime):
        """Create string representation of the selection for drag-n-drop"""
        sSelectData = self.get_selection_as_string()
        if sSelectData == '':
            return
        oSelection_data.set(oSelection_data.target, 8, sSelectData)

    def split_selection_data(self, sSelectionData):
        """Helper function to subdivide selection string into bits again"""
        if sSelectionData == '':
            return 'None', ['']
        aLines = sSelectionData.splitlines()
        sSource = aLines[0]
        if sSource == "Sutekh Pane:":
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

    # pylint: disable-msg=R0913, W0613
    # arguments as required by the function signature
    def drag_delete(self, oBtn, oContext, oData):
        """Default drag-delete handler"""
        pass

    def card_drop(self, oWdgt, oContext, iXPos, iYPos, oData, oInfo, oTime):
        """Default drag-n-drop handler."""
        # Pass off to the Frame Handler
        self._oController.frame.drag_drop_handler(oWdgt, oContext, iXPos,
                iYPos, oData, oInfo, oTime)

    def add_paste_data(self, sSource, aCards):
        """Helper function for copy+paste and drag+drop.

           Handle the heavy lifting of adding cards to the actual card
           list model, and so on.
           """
        return False # do nothing

class EditableCardListView(CardListView):
    """CardList View which can be edited.

       Add support for displaying number changing buttons,
       setting the editable style, and so forth."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oController, oWindow, oModel):
        super(EditableCardListView, self).__init__(oController, oWindow,
                oModel)

        # Setup columns for default view
        oCell1 = gtk.CellRendererText()
        oCell1.set_property('style', pango.STYLE_ITALIC)
        oCell2 = gtk.CellRendererText()
        oCell2.set_property('style', pango.STYLE_ITALIC)

        oColumn1 = gtk.TreeViewColumn("#", oCell1, text=1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(40)
        oColumn1.set_sort_column_id(1)
        self.append_column(oColumn1)

        oColumn2 = gtk.TreeViewColumn("Cards", oCell2, text=0)
        oColumn2.set_expand(True)
        oColumn2.set_sort_column_id(0)
        self.append_column(oColumn2)

        # Arrow cells
        oCell3 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_ADD, self)
        oCell4 = CellRendererSutekhButton()
        oCell4.load_icon(gtk.STOCK_REMOVE, self)

        oColumn3 = gtk.TreeViewColumn("", oCell3, showicon=2)
        oColumn3.set_fixed_width(22)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn3)

        oColumn4 = gtk.TreeViewColumn("", oCell4, showicon=3)
        oColumn4.set_fixed_width(22)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4)

        oCell3.connect('clicked', self.inc_card)
        oCell4.connect('clicked', self.dec_card)

        self.connect('map-event', self.mapped)

        self._oMenuEditWidget = None

        self.set_expander_column(oColumn2)

    def load(self):
        """Called when the model needs to be reloaded."""
        self._oModel.load()
        if self.get_parent(): # This isn't true when creating the card list
            self.check_editable()

    def check_editable(self):
        """Set the card list to be editable if it's empty"""
        if self._oModel.get_card_iterator(None).count() == 0:
            self._set_editable(True)

    # Used by card dragging handlers
    def add_card(self, sCardName, sExpansion):
        """Called to add a card with expansion"""
        if self._oModel.bEditable:
            self._oController.add_card(sCardName, sExpansion)

    # When editing cards, we pass info to the controller to
    # update stuff in the database
    # The Controller is responsible for updating the model,
    # since it defines the logic for handling expansions, etc.

    # pylint: disable-msg=W0613
    # arguments as required by the function signature
    def inc_card(self, oCell, oPath):
        """Called to increment the count for a card."""
        if self._oModel.bEditable:
            # pylint: disable-msg=W0612
            # only interested in bInc
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bInc:
                sCardName = self._oModel.get_card_name_from_path(oPath)
                sExpansion = self._oModel.get_exp_name_from_path(oPath)
                self._oController.inc_card(sCardName, sExpansion)

    def dec_card(self, oCell, oPath):
        """Called to decrement the count for a card"""
        if self._oModel.bEditable:
            # pylint: disable-msg=W0612
            # only interested in bDec
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bDec:
                sCardName = self._oModel.get_card_name_from_path(oPath)
                sExpansion = self._oModel.get_exp_name_from_path(oPath)
                self._oController.dec_card(sCardName, sExpansion)

    # functions related to tweaking widget display

    def mapped(self, oWidget, oEvent):
        """Called when the view has been mapped, so we can twiddle the
           display"""
        # see if we need to be editable
        self.check_editable()

    # pylint: enable-msg=W0613

    def set_color_edit_cue(self):
        """Set a visual cue that the card set is editable."""
        oCurStyle = self.rc_get_style()
        self.set_name('editable_view')
        oParent = self.get_parent()
        oDefaultSutekhStyle = gtk.rc_get_style_by_paths(self.get_settings(),
                oParent.path()+'.', oParent.class_path(),
                oParent)
        oSpecificStyle = self.rc_get_style()
        if oSpecificStyle == oDefaultSutekhStyle or \
                oDefaultSutekhStyle is None:
            # No specific style set
            oMap = self.get_colormap()
            sColour = 'red'
            if oMap.alloc_color(sColour).pixel == \
                    oCurStyle.fg[gtk.STATE_NORMAL].pixel:
                sColour = 'green'
            sStyleInfo = """
            style "internal_sutekh_editstyle" {
                fg[NORMAL] = "%(colour)s"
                }
            widget "%(path)s" style "internal_sutekh_editstyle"
            """ % { 'colour' : sColour, 'path' : self.path() }
            gtk.rc_parse_string(sStyleInfo)
            # Need to force re-assesment of styles
            self.set_name('editable_view')

    def set_color_normal(self):
        """Unset the editable visual cue"""
        self.set_name('normal_view')

    def _set_editable(self, bValue):
        """Update the view and menu when the editable status changes"""
        self._oModel.bEditable = bValue
        if self._oMenuEditWidget is not None:
            self._oMenuEditWidget.set_active(bValue)
        if bValue:
            self.set_color_edit_cue()
        else:
            self.set_color_normal()

    def toggle_editable(self, bValue):
        """Reload the view and update status when editable status changes"""
        self._set_editable(bValue)
        self.reload_keep_expanded()

    def set_edit_menu_item(self, oMenuWidget):
        """Keep track of the menu item, so we can update it's toggled
           status."""
        self._oMenuEditWidget = oMenuWidget

