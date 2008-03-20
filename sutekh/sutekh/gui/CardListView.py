# CardListView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, pango
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton

class CardListViewListener(object):
    """
    Listens to changes, i.e. .set_card_text(...)
    to CardListViews.
    """
    def set_card_text(self, sCardName, sExpansion):
        """
        The CardListViw has called set_card_text on the CardText pane
        """
        pass

class CardListView(gtk.TreeView, object):
    def __init__(self, oController, oMainWindow, oConfig, oModel):
        self._oModel = oModel
        self._oC = oController
        self._oMainWin = oMainWindow
        self._oConfig = oConfig


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

    # Listener helper functions

    def add_listener(self, oListener):
        self.dListeners[oListener] = None

    def remove_listener(self, oListener):
        del self.dListeners[oListener]


    def column_clicked(self, oColumn):
        self.emit('button-press-event',
                gtk.gdk.Event(gtk.gdk.BUTTON_PRESS_MASK))
        return False

    def load(self):
        """
        Called when the model needs to be reloaded.
        """
        self._oModel.load()

    # Help functions used by reload_keep_expanded
    def __get_row_status(self, oModel, oPath, oIter, dExpandedDict):
        if self.row_expanded(oPath):
            dExpandedDict.setdefault(oPath,
                    self._oModel.getCardNameFromPath(oPath))
        return False # Need to process the whole list

    def __set_row_status(self, dExpandedDict):
        for oPath in dExpandedDict:
            try:
                sCardName = self._oModel.getCardNameFromPath(oPath)
                if sCardName == dExpandedDict[oPath]:
                    self.expand_to_path(oPath)
            except ValueError:
                # Paths may disappear, so this error can be ignored
                pass
        return False

    def reload_keep_expanded(self):
        """
        Attempt to reload the card list, keeping the existing
        structure of expanded rows
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

    def getWindow(self): return self._oMainWin
    def getModel(self): return self._oModel
    def getController(self): return self._oC

    # Activating Rows

    def card_activated(self, wTree, oPath, oColumn):
        sCardName = self._oModel.getCardNameFromPath(oPath)
        self._oC.set_card_text(sCardName)
        for oListener in self.dListeners:
            oListener.set_card_text(sCardName, '')

    # Key combinations

    def key_released(self, oWidget, oEvent):
        if oEvent.get_state() == gtk.gdk.CONTROL_MASK:
            if oEvent.string == '+':
                self.expand_all()
                return True
            elif oEvent.string == '-':
                self.collapse_all()
                return True
        # Let other key handles take charge
        return False

    # Selecting

    def force_cursor_move(self, treeview, step, count):
        """
        Special handling for move events for buggy gtk events. 
        We need to allow the selection of top level items when 
        moving the cursor over them
        """
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

    def can_select(self, oPath):
        """disable selecting top level rows"""
        if self.bSelectTop > 0:
            # Buggy gtk version work-around
            self.bSelectTop -= 1
            return True 
        # In general, we don't allow the top level nodes to be selected
        return self._oModel.iter_parent(self._oModel.get_iter(oPath)) is not None

    def card_selected(self, oSelection):
        if self.bReentrant:
            # This is here because we alter the selection inside
            # this function (resulting in a nested call).
            # self.bReentrant is set and unset below.
            return False

        # If the selection is empty, clear everything and return
        if oSelection.count_selected_rows() <= 0:
            self._aOldSelection = []
            return False

        oModel, aList = oSelection.get_selected_rows()

        # Non default selection behaviour. If we have multiple rows selected,
        # and the user selects a single row that is in the selection, we
        # DON'T change the selection
        tCursorPos = self.get_cursor()
        if len(aList) == 1 and len(self._aOldSelection) > 1 and \
            tCursorPos[0] == aList[0] and aList[0] in self._aOldSelection:
            # reset the list to it's previous state, but set
            # displayed card to this one
            try:
                self.bReentrant = True
                for oP in self._aOldSelection:
                    oSelection.select_path(oP)
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

        sCardName = self._oModel.getCardNameFromPath(oPath)
        self._oC.set_card_text(sCardName)
        sExpansion = self._oModel.getExpansionNameFromPath(oPath)
        if not sExpansion:
            sExpansion = ''
        for oListener in self.dListeners:
            oListener.set_card_text(sCardName, sExpansion)

    # Card name searching

    def compare(self, oModel, iColumn, sKey, oIter, oData):
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
                    sChildName = self._oModel.getNameFromIter(oChildIter).lower()
                    if sChildName.startswith(sKey.lower()):
                        # Expand the row
                        self.expand_to_path(oPath)
                        # Bail out, as compare will find the match for us
                        return True
                return True # No matches, so bail

        sCardName = self._oModel.getNameFromIter(oIter).lower()
        if sCardName.startswith(sKey.lower()):
            return False

        return True

    # Filtering

    def getFilter(self, oMenu):
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWin,
                    self._oConfig, self._oC.filtertype)

        self._oFilterDialog.run()

        if self._oFilterDialog.Cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.getFilter()
        if oFilter != None:
            self._oModel.selectfilter = oFilter
            if not self._oModel.applyfilter:
                # If a filter is set, automatically apply
                oMenu.setApplyFilter(True)
            else:
                # Filter Changed, so reload
                self.load()
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if self._oModel.applyfilter:
                oMenu.setApplyFilter(False)
            else:
                self.load()

    def runFilter(self, bState):
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self.load()

    def process_selection(self):
        """
        Create a dictionary from the selection.
        with entries of the form sCardName : {sExpansion1 : iCount1, ... }
        for use in drag-'n drop and elsewhere
        """
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            sCardName, sExpansion, iCount, iDepth = \
                    oModel.get_all_from_path(oPath)
            if iDepth == 0:
                # Skip top level items, since they're meaningless for the selection
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

    # Drag and Drop
    # Sub-classes should override as needed.

    def drag_card(self, btn, context, selection_data, info, time):
        """
        Create string represntation of the sec ltion for drag-n-drop code
        """
        if self._oSelection.count_selected_rows()<1:
            return
        dSelectedData = self.process_selection()
        # Create selection data structure
        # Need to bung everything into a string, alas
        sSelectData = self.sDragPrefix
        for sCardName in dSelectedData:
            for sExpansion, iCount in dSelectedData[sCardName].iteritems():
                sSelectData = sSelectData + "\n" + \
                        str(iCount) + '\n' + \
                        sCardName + "\n" + sExpansion
        selection_data.set(selection_data.target, 8, sSelectData)

    def split_selection_data(self, sSelectionData):
        """Helper function to subdivide selection string into bits again"""
        aLines = sSelectionData.splitlines()
        sSource = aLines[0]
        if sSource == "Sutekh Pane:":
            return sSource, aLines
        # Construct list of (iCount, sCardName, sExpansion) tuples
        def true_expansion(sExpand):
            """Convert back from the 'None' for None placeholder in the string"""
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

    def drag_delete(self, btn, context, data):
        pass

    def card_drop(self, w, context, x, y, data, info, time):
        # Pass off to the Frame Handler
        self._oC.frame.drag_drop_handler(w, context, x, y, data, info, time)

class EditableCardListView(CardListView):
    def __init__(self, oController, oWindow, oConfig, oModel):
        super(EditableCardListView, self).__init__(oController, oWindow,
                oConfig, oModel)

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

        oColumn1.connect('clicked', self.column_clicked)

        oColumn2 = gtk.TreeViewColumn("Cards", oCell2, text=0)
        oColumn2.set_expand(True)
        oColumn2.set_sort_column_id(0)
        self.append_column(oColumn2)
        oColumn2.connect('clicked', self.column_clicked)

        # Arrow cells
        oCell3 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_GO_UP, self)
        oCell4 = CellRendererSutekhButton()
        oCell4.load_icon(gtk.STOCK_GO_DOWN, self)

        oColumn3 = gtk.TreeViewColumn("", oCell3, showicon=2)
        oColumn3.set_fixed_width(20)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn3)

        oColumn4 = gtk.TreeViewColumn("", oCell4, showicon=3)
        oColumn4.set_fixed_width(20)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4)

        oCell3.connect('clicked', self.incCard)
        oCell4.connect('clicked', self.decCard)

        self.set_expander_column(oColumn2)
        if hasattr(self, 'set_grid_lines'):
            self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)

    # Used by card dragging handlers
    def addCard(self, sCardName, sExpansion):
        if self._oModel.bEditable:
            bSucc = self._oC.addCard(sCardName, sExpansion)

    # When editing cards, we pass info to the controller to
    # update stuff in the database
    # The Controller is responsible for updating the model,
    # since it defines the logic for handling expansions, etc.

    def incCard(self, oCell, oPath):
        if self._oModel.bEditable:
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bInc:
                sCardName = self._oModel.getCardNameFromPath(oPath)
                sExpansion = self._oModel.getExpansionNameFromPath(oPath)
                self._oC.incCard(sCardName, sExpansion)

    def decCard(self, oCell, oPath):
        if self._oModel.bEditable:
            bInc, bDec = self._oModel.get_inc_dec_flags_from_path(oPath)
            if bDec:
                sCardName = self._oModel.getCardNameFromPath(oPath)
                sExpansion = self._oModel.getExpansionNameFromPath(oPath)
                self._oC.decCard(sCardName, sExpansion)

    def set_color_edit_cue(self):
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
        self.set_name('normal_view')

