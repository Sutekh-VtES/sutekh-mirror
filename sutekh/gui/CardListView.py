# CardListView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, pango
from sutekh.gui.CardListModel import CardListModel
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.PopupMenu import PopupMenu
from sutekh.gui.CellRendererSutekhButton import CellRendererSutekhButton

class CardListView(gtk.TreeView, object):
    def __init__(self, oController, oMainWindow, oConfig):
        self._oModel = CardListModel()
        self._oC = oController
        self._oMainWin = oMainWindow
        self._oConfig = oConfig

        super(CardListView,self).__init__(self._oModel)

        # Selecting rows
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_MULTIPLE)
        self._aOldSelection = []

        self._oSelection.connect('changed',self.cardSelected)

        # Activating rows
        self.connect('row-activated',self.cardActivated)

        # Text searching of card names
        self.set_search_equal_func(self.compare,None)
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

        self.connect('drag_data_get',self.dragCard)
        self.connect('drag_data_delete',self.dragDelete)
        self.connect('drag_data_received',self.cardDrop)
        self.bReentrant = False

        # Filtering Dialog
        self._oFilterDialog = None

    def load(self):
        """
        Called when the model needs to be reloaded.
        """
        self._oModel.load()

    # Introspection

    def getWindow(self): return self._oMainWin
    def getModel(self): return self._oModel
    def getController(self): return self._oC

    # Activating Rows

    def cardActivated(self,wTree,oPath,oColumn):
        sCardName = self._oModel.getCardNameFromPath(oPath)
        self._oC.setCardText(sCardName)

    # Selecting

    def cardSelected(self,oSelection):
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
            # prune any root nodes from the selection
            for oP in aList:
                if not oModel.iter_parent(oModel.get_iter(oP)):
                    oSelection.unselect_path(oP)

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
        self._oC.setCardText(sCardName)

    # Card name searching

    def compare(self,oModel,iColumn,sKey,oIter,oData):
        if oModel.iter_depth(oIter) == 0 or oModel.iter_depth(oIter) == 2:
            # Don't succeed for top level items or expansion items
            return True

        sCardName = self._oModel.getNameFromIter(oIter).lower()
        if sCardName.startswith(sKey.lower()):
            return False

        return True

    # Filtering

    def getFilter(self, oMenu):
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWin, self._oConfig, self._oC.filtertype)

        self._oFilterDialog.run()

        if self._oFilterDialog.Cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.getFilter()
        if oFilter != None:
            self._oModel.selectfilter = oFilter
            if not self._oModel.applyfilter:
                oMenu.setApplyFilter(True) # If a filter is set, automatically apply
                #self.runFilter(True)
            else:
                self.load() # Filter Changed, so reload
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            oMenu.setApplyFilter(False)
            #self.runFilter(False)
            self.load()

    def runFilter(self, bState):
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self.load()

    # Drag and Drop
    # Sub-classes should override as needed.

    def dragCard(self, btn, context, selection_data, info, time):
        if self._oSelection.count_selected_rows()<1:
            return
        oModel, oPathList = self._oSelection.get_selected_rows()
        dSelectedData = {}
        for oPath in oPathList:
            sCardName, sExpansion, iCount, iDepth = oModel.getAllFromPath(oPath)
            if iDepth == 0:
                # Skip top level items, since dragging them is meaningless
                continue
            # if a card is selected, and some of it's children (which are
            # the expansions) are selected, the top-level selection is updated
            # to account for the children selection
            dSelectedData.setdefault(sCardName,{})
            if iDepth == 1:
                dSelectedData[sCardName]['0'] = iCount
            else:
                dSelectedData[sCardName][sExpansion] = iCount
                if '0' in dSelectedData[sCardName].keys():
                    dSelectedData[sCardName]['0'] -= iCount
                    if dSelectedData[sCardName]['0'] == 0:
                        # dSelectedData[sCardName]['0'] < 0 shouldn't
                        # be possible 
                        # All children selected, so remove from selection
                        del dSelectedData[sCardName]['0']
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
        # Construct list of (iCount, sCardName, sExpansion) tuples
        aCardInfo = zip(aLines[1::3],aLines[2::3],aLines[3::3])
        return sSource, aCardInfo

    def dragDelete(self, btn, context, data):
        pass

    def cardDrop(self, w, context, x, y, data, info, time):
        pass

class EditableCardListView(CardListView):
    def __init__(self, oController, oWindow, oConfig):
        super(EditableCardListView,self).__init__(oController, oWindow, oConfig)

        # Setup columns for default view
        oCell1 = gtk.CellRendererText()
        oCell1.set_property('style', pango.STYLE_ITALIC)
        oCell2 = gtk.CellRendererText()
        oCell2.set_property('style', pango.STYLE_ITALIC)

        oColumn1 = gtk.TreeViewColumn("#",oCell1,text=1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(40)
        oColumn1.set_sort_column_id(1)
        self.append_column(oColumn1)

        oColumn2 = gtk.TreeViewColumn("Cards",oCell2,text=0)
        oColumn2.set_expand(True)
        oColumn2.set_sort_column_id(0)
        self.append_column(oColumn2)

        # Arrow cells
        oCell3 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_GO_UP,self)
        oCell4 = CellRendererSutekhButton()
        oCell4.load_icon(gtk.STOCK_GO_DOWN,self)

        oColumn3 = gtk.TreeViewColumn("",oCell3,showicon=2)
        oColumn3.set_fixed_width(20)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn3)

        oColumn4 = gtk.TreeViewColumn("",oCell4,showicon=3)
        oColumn4.set_fixed_width(20)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4)

        oCell3.connect('clicked',self.incCard)
        oCell4.connect('clicked',self.decCard)

        self.set_expander_column(oColumn2)
        if hasattr(self,'set_grid_lines'):
            self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
     
    # Used by card dragging handlers
    def addCard(self,sCardName):
        if self._oModel.bEditable:
            bSucc = self._oC.addCard(sCardName)

    # When editing cards, we pass info to the controller to
    # update stuff in the database, and rely on the model
    # watching events on the database to update itself and the 
    # view. This uses the SQLObject events to ensure
    # multiple views of the database are kept in sync.

    def incCard(self,oCell,oPath):
        if self._oModel.bEditable:
            sCardName = self._oModel.getCardNameFromPath(oPath)
            sExpansion = self._oModel.getExpansionNameFromPath(oPath)
            bSucc = self._oC.incCard(sCardName, sExpansion)

    def decCard(self,oCell,oPath):
        if self._oModel.bEditable:
            sCardName = self._oModel.getCardNameFromPath(oPath)
            sExpansion = self._oModel.getExpansionNameFromPath(oPath)
            bSucc = self._oC.decCard(sCardName, sExpansion)
