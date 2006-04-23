# CardListView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, gobject

class CardListView(gtk.TreeView,object):
    def __init__(self,oController):
        self._oModel = gtk.TreeStore(gobject.TYPE_STRING,gobject.TYPE_INT)
    
        super(CardListView,self).__init__(self._oModel)
        self._oC = oController
        
        self.set_size_request(200, -1)
        
        self._oSelection = self.get_selection()
        self._oSelection.set_mode(gtk.SELECTION_MULTIPLE)
        self.__oldSelection = []
        
        self.connect('row-activated',self.cardActivated)
        self._oSelection.connect('changed',self.cardSelected)

        self.expand_all()
        
    def cardActivated(self,wTree,oPath,oColumn):
        oModel = wTree.get_model()
        oIter = oModel.get_iter(oPath)
        sCardName = oModel.get_value(oIter,0)
        self._oC.setCardText(sCardName)
    
    def cardSelected(self,oSelection):
        if oSelection.count_selected_rows()<1:
            return False
        oModel, List = oSelection.get_selected_rows()
        if len(List)<=len(self.__oldSelection):
           oIter=oModel.get_iter(List[-1])
        else:
            # Find the last entry in List that's not in __oldSelection
            s=[x for x in List if x not in self.__oldSelection]
            oIter=oModel.get_iter(s[-1])
        sCardName = oModel.get_value(oIter,0)
        self._oC.setCardText(sCardName)
        self.__oldSelection=List

    def compare(self,model,column,key,iter,data):
        CandName=model.get_value(iter,0).lower()
        if CandName.startswith(key.lower()):
            return False
        return True
