import gtk, pango
from CardListView import CardListView
from SutekhObjects import *

class AbstractCardView(CardListView):
    def __init__(self,oController):
        super(AbstractCardView,self).__init__(oController)

        # HouseKeeping work for 
    
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
        
        self.load()
        
    def dragCard(self, btn, context, selection_data, info, time):
        oModel, oIter = self._oSelection.get_selected()
        if not oIter:
            return
        sCardName = oModel.get_value(oIter,0)
        selection_data.set(selection_data.target, 8, "Abst:" + sCardName)
    
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
            for oCard in oType.cards:
                oChildIter = self._oModel.append(oSectionIter)
                self._oModel.set(oChildIter,
                    0, oCard.name,
                    1, 0
                )
