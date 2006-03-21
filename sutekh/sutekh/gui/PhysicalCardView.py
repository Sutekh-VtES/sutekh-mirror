import gtk, gobject, pango
from CardListView import CardListView
from CellRendererSutekhButton import CellRendererSutekhButton
from SutekhObjects import *
from Filters import *
from Groupings import *
from FilterDialog import FilterDialog
from PopupMenu import PopupMenu

class PhysicalCardView(CardListView):
    def __init__(self,oController,oWindow):
        super(PhysicalCardView,self).__init__(oController)
        self.__oWin=oWindow
        
        oCell1 = gtk.CellRendererText()
        oCell1.set_property('style', pango.STYLE_ITALIC)
        oCell2 = gtk.CellRendererText()
        oCell2.set_property('style', pango.STYLE_ITALIC)
        oCell3 = CellRendererSutekhButton()
        oCell4 = CellRendererSutekhButton()
        oCell3.load_icon(gtk.STOCK_GO_UP,self)
        oCell4.load_icon(gtk.STOCK_GO_DOWN,self)
        #oCell3 = gtk.CellRendererToggle()
        #oCell4 = gtk.CellRendererToggle()
        
        oColumn1 = gtk.TreeViewColumn("#",oCell1,text=1)
        self.append_column(oColumn1)
        oColumn1.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        oColumn1.set_fixed_width(40)
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
     
        oCell3.connect('clicked',self.incCard)
        oCell4.connect('clicked',self.decCard)

        aTargets = [ ('STRING', 0, 0), # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here

        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                  aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL, aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get',self.dragCard)
        self.connect('drag_data_delete',self.dragDelete)
        self.connect('drag_data_received',self.cardDrop)
        self.connect('button_press_event',self.pressButton)

        self.set_search_equal_func(self.compare,None)
        self.set_search_column(1)
        self.set_enable_search(True)

        self.Filter = None
        self.doFilter = False
        self.FilterDialog = None

        self.load()
               
    def incCard(self,oCell,oPath):
        oIter = self._oModel.get_iter(oPath)
        sCardName = self._oModel.get_value(oIter,0)
        self._oC.incCard(sCardName)
    
    def decCard(self,oCell,oPath):
        oIter = self._oModel.get_iter(oPath)
        sCardName = self._oModel.get_value(oIter,0)
        self._oC.decCard(sCardName)
    
    def cardDrop(self, w, context, x, y, data, info, time):
        if data and data.format == 8 and data.data[:5] == "Abst:":
            cards=data.data.splitlines()
            for name in cards[1:]:
                self._oC.addCard(name)
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)
    
    def dragCard(self, btn, context, selection_data, info, time):
        if self._oSelection.count_selected_rows()<1:
            return
        oModel, oPathList = self._oSelection.get_selected_rows()
        selectData = "Phys:"
        for oPath in oPathList:
            oIter = oModel.get_iter(oPath)
            sCardName = oModel.get_value(oIter,0)
            selectData = selectData + "\n" + sCardName
        selection_data.set(selection_data.target, 8, selectData)

    def dragDelete(self, btn, context, data):
        pass

    def load(self):
        self._oModel.clear()
	
        # Set Filter
        if self.doFilter:
            oFilter = self.Filter.getExpression()
        else:
            oFilter = PhysicalCardFilter().getExpression()
		
        # Set Grouping
        cGroupBy = CardTypeGrouping
		
        # Set Physical Card Iterable
        oPhysCardIter = PhysicalCard.select(oFilter).distinct()

        # Count by Abstract Card
        dAbsCards = {}
        for oCard in oPhysCardIter:
            dAbsCards.setdefault(oCard.abstractCard,0)
            dAbsCards[oCard.abstractCard] += 1
         
        aCards = list(dAbsCards.iteritems())
        aCards.sort(lambda x,y: cmp(x[0].name,y[0].name))
 		
        # Iterate over groups
        for sGroup, oGroupIter in cGroupBy(aCards,lambda x:x[0]):
            # Check for null group
            if sGroup is None:
                sGroup = '<< None >>'
        		
            # Create Group Section
            oSectionIter = self._oModel.append(None)
			
            # Fill in Cards
            iGrpCnt = 0
            for oCard, iCnt in oGroupIter:
                iGrpCnt += iCnt
                oChildIter = self._oModel.append(oSectionIter)
                self._oModel.set(oChildIter,
                    0, oCard.name,
                    1, iCnt
                )
                
            # Update Group Section
            self._oModel.set(oSectionIter,
                0, sGroup,
                1, iGrpCnt
            )

        self.expand_all()

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
   
    def getFilter(self,Menu,Window):
        if self.FilterDialog is None:
            self.FilterDialog=FilterDialog(self.__oWin)
        self.FilterDialog.run()
        if self.FilterDialog.Cancelled():
            return # Change nothing
        Filter = self.FilterDialog.getFilter()
        if Filter != None:
            self.Filter=FilterAndBox([Filter,PhysicalCardFilter()])
            if not self.doFilter:
                Menu.setApplyFilter(True) # If a filter is set, automatically apply
                self.runFilter(True)
            else:
                self.load() # Filter Changed, so reload
        else:
            Menu.setApplyFilter(False) 
            self.runFilter(False)
            self.load()
        
    def runFilter(self,state):
        if self.doFilter != state:
            self.doFilter=state
            self.load()
