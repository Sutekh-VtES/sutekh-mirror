import gtk, gobject

class CardListView(gtk.TreeView,object):
    def __init__(self,oController):
        self._oModel = gtk.TreeStore(gobject.TYPE_STRING,gobject.TYPE_INT)
    
        super(CardListView,self).__init__(self._oModel)
        self._oC = oController
        
        self.set_size_request(200, -1)
        
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_BROWSE)
        
        self.connect('row-activated',self.cardActivated)
        self._oSelection.connect('changed',self.cardSelected)

        self.expand_all()
        
    def cardActivated(self,wTree,oPath,oColumn):
        oModel = wTree.get_model()
        oIter = oModel.get_iter(oPath)
        sCardName = oModel.get_value(oIter,0)
        self._oC.setCardText(sCardName)
    
    def cardSelected(self,oSelection):
        oModel, oIter = oSelection.get_selected()
        if not oIter:
            return False
        sCardName = oModel.get_value(oIter,0)
        self._oC.setCardText(sCardName)

    def compare(self,model,column,key,iter,data):
        CandName=model.get_value(iter,0).lower()
        if CandName.startswith(key.lower()):
            return False
        return True
