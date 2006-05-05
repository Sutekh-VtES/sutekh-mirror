# AbstractCardView.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk, pango
from CardListView import CardListView

class AbstractCardView(CardListView):
    def __init__(self,oController,oWindow):
        super(AbstractCardView,self).__init__(oController,oWindow)
            
        oCell = gtk.CellRendererText()
        oCell.set_property('style', pango.STYLE_ITALIC)
        oColumn = gtk.TreeViewColumn("Collection", oCell, text=0)
        self.append_column(oColumn)
                
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
