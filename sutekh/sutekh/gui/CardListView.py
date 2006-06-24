# CardListView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, pango
from CardListModel import CardListModel
from FilterDialog import FilterDialog
from PopupMenu import PopupMenu
from CellRendererSutekhButton import CellRendererSutekhButton

class CardListView(gtk.TreeView,object):
    def __init__(self,oController,oWindow):
        self._oModel = CardListModel()
        self._oC = oController
        self._oWin = oWindow

        super(CardListView,self).__init__(self._oModel)
        
        self.set_size_request(200, -1)
        
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

        # Filtering Dialog
        self._oFilterDialog = None

    def load(self):
        """
        Called when the model needs to be reloaded.
        """
        self._oModel.load()

    # Introspection
    
    def getWindow(self): return self._oWin
    def getModel(self): return self._oModel

    # Activating Rows
        
    def cardActivated(self,wTree,oPath,oColumn):
        sCardName = self._oModel.getCardNameFromPath(oPath)
        self._oC.setCardText(sCardName)
    
    # Selecting
    
    def cardSelected(self,oSelection):
        if oSelection.count_selected_rows() <= 0:
            return False
            
        oModel, aList = oSelection.get_selected_rows()
        
        if len(aList) <= len(self._aOldSelection):
           oPath = aList[-1]
        else:
            # Find the last entry in aList that's not in _aOldSelection
            oPath = [x for x in aList if x not in self._aOldSelection][-1]
            
        sCardName = self._oModel.getCardNameFromPath(oPath)
        self._oC.setCardText(sCardName)
        self._aOldSelection = aList

    # Card name searching

    def compare(self,oModel,iColumn,sKey,oIter,oData):
        if oModel.iter_depth(oIter) == 0:
            # Don't succeed for top level items
            return True
            
        sCardName = self._oModel.getCardNameFromIter(oIter).lower()
        if sCardName.startswith(sKey.lower()):
            return False
            
        return True

    # Filtering

    def getFilter(self,oMenu):
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oWin)
            
        self._oFilterDialog.run()
        
        if self._oFilterDialog.Cancelled():
            return # Change nothing
            
        oFilter = self._oFilterDialog.getFilter()
        if oFilter != None:
            self._oModel.selectfilter = oFilter
            if not self._oModel.applyfilter:
                oMenu.setApplyFilter(True) # If a filter is set, automatically apply
                self.runFilter(True)
            else:
                self.load() # Filter Changed, so reload
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            oMenu.setApplyFilter(False) 
            self.runFilter(False)
            self.load()

    def runFilter(self,bState):
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self.load()

    # Drag and Drop
    # Sub-classes should override as needed.
    
    def dragCard(self, btn, context, selection_data, info, time):
        pass

    def dragDelete(self, btn, context, data):
        pass

    def cardDrop(self, w, context, x, y, data, info, time):
        pass

    
class EditableCardListView(CardListView):
    def __init__(self,oController,oWindow):
        super(EditableCardListView,self).__init__(oController,oWindow)
    
        oCell1 = gtk.CellRendererText()
        oCell1.set_property('style', pango.STYLE_ITALIC)
        oCell2 = gtk.CellRendererText()
        oCell2.set_property('style', pango.STYLE_ITALIC)
        oCell3 = CellRendererSutekhButton()
        oCell4 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_GO_UP,self)
        oCell4.load_icon(gtk.STOCK_GO_DOWN,self)
        
        oColumn1 = gtk.TreeViewColumn("#",oCell1,text=1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(40)
        self.append_column(oColumn1)
        
        oColumn2 = gtk.TreeViewColumn("Cards", oCell2, text=0)
        oColumn2.set_expand(True)
        self.append_column(oColumn2)
        
        oColumn3 = gtk.TreeViewColumn("",oCell3)
        oColumn3.set_fixed_width(20)
        oColumn3.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn3)
        
        oColumn4 = gtk.TreeViewColumn("",oCell4)
        oColumn4.set_fixed_width(20)
        oColumn4.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.append_column(oColumn4) 

        self.set_expander_column(oColumn2)
     
        # Button Clicks
        oCell3.connect('clicked',self.incCard)
        oCell4.connect('clicked',self.decCard)      
        self.connect('button_press_event',self.pressButton)

    # Card Inc and Dec

    def incCard(self,oCell,oPath):
        sCardName = self._oModel.getCardNameFromPath(oPath)
        bSucc = self._oC.incCard(sCardName)
        if bSucc:
            self._oModel.incCard(oPath)
    
    def decCard(self,oCell,oPath):
        sCardName = self._oModel.getCardNameFromPath(oPath)
        bSucc = self._oC.decCard(sCardName)
        if bSucc:
            self._oModel.decCard(oPath)

    def addCard(self,sCardName):
        bSucc = self._oC.addCard(sCardName)
        if bSucc:
            self._oModel.incCardByName(sCardName)

    # Popup Menu

    def pressButton(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo != None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, False)
                popupMenu=PopupMenu(self,path)
                popupMenu.popup( None, None, None, event.button, time)
                return True # Don't propogate to buttons
        return False
