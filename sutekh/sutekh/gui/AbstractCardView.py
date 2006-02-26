import gtk, pango
from CardListView import CardListView
from SutekhObjects import *
from FilterDialog import FilterDialog
from Filters import *

class AbstractCardView(CardListView):
    def __init__(self,oController,oWindow):
        super(AbstractCardView,self).__init__(oController)

        # HouseKeeping work for 
    
        self.__oWin=oWindow
        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)
        oColumn = gtk.TreeViewColumn("Collection", oCell, text=0)
        self.append_column(oColumn)
        
        aTargets = [ ('STRING', 0, 0), # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here
        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                  aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        self.connect('drag_data_get',self.dragCard)
        self.connect('drag_data_delete',self.dragDelete)
        self.set_search_equal_func(self.compare,None)
        self.set_search_column(0)
        self.set_enable_search(True)
        self.doFilter = False
        self.Filter = None
        self.FilterDialog = None
        
        self.load()
        
    def dragCard(self, btn, context, selection_data, info, time):
        if self._oSelection.count_selected_rows()<1:
            return
        oModel, oPathList = self._oSelection.get_selected_rows()
        selectData = "Abst:"
        for oPath in oPathList:
            oIter = oModel.get_iter(oPath)
            sCardName = oModel.get_value(oIter,0)
            selectData = selectData + "\n" + sCardName
        selection_data.set(selection_data.target, 8, selectData)
    
    def dragDelete(self, btn, context, data):
        pass

    def compare(self,model,column,key,iter,data):
        if (model.iter_depth(iter)==0):
            # Don't succeed for top level items
            return True
        CandName=model.get_value(iter,0).lower()
        if CandName.startswith(key.lower()):
            return False
        return True
        
    def load(self):
        self._oModel.clear()
        for oType in CardType.select():
            # Create Section
            oSectionIter = self._oModel.append(None)
            self._oModel.set(oSectionIter,
                0, oType.name,
                1, 0
            )
            # Fill in Cards
            if self.doFilter and self.Filter != None:
                cardList = AbstractCard.select(
                    FilterAndBox([CardTypeFilter(oType.name),self.Filter]).getExpression()
		).distinct()
            else:
                cardList=oType.cards
            for oCard in cardList:
                oChildIter = self._oModel.append(oSectionIter)
                self._oModel.set(oChildIter,
                    0, oCard.name,
                    1, 0
                )
        
    def getFilter(self,MainMenu):
        if self.FilterDialog is None:
            self.FilterDialog=FilterDialog(self.__oWin)
        self.FilterDialog.run()
        if self.FilterDialog.Cancelled():
            return # Change nothing
        Filter = self.FilterDialog.getFilter()
        if Filter != None:
            self.Filter=Filter
            if not self.doFilter:
                MainMenu.setApplyFilter(True) # If a filter is set, automatically apply
                self.runFilter(True)
            else:
                self.load() # Filter Changed, so reload
        else:
            MainMenu.setApplyFilter(False) 
            self.runFilter(False)
            self.load()
        

    def runFilter(self,state):
        if self.doFilter != state:
            self.doFilter=state
            self.load()
