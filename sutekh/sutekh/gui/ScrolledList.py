# ScrolledList.py
# Scrolled List, used in the Filter Dialo and elsewhere
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class ScrolledList(gtk.Frame):
    def __init__(self,title,sNullValue=None):
        super(ScrolledList,self).__init__(None)
        self.List=gtk.ListStore(gobject.TYPE_STRING)
        self.TreeView=gtk.TreeView(self.List)
        self.TreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        myScroll=AutoScrolledWindow(self.TreeView)
        self.add(myScroll)
        oCell1=gtk.CellRendererText()
        self.sNullValue=sNullValue
        oColumn=gtk.TreeViewColumn(title,oCell1,text=0)
        iter=self.List.append(None) # Create Null item at top of list
        if self.sNullValue is not None:
            self.List.set(iter,0,self.sNullValue)
        self.TreeView.append_column(oColumn)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    def set_select_single(self):
        self.TreeView.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def set_select_multiple(self):
        self.TreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    def get_list(self):
        return self.List

    def get_view(self):
        return self.TreeView

    def reset(self,State):
        Model=self.TreeView.get_model()
        oIter=Model.get_iter_first()
        while oIter != None:
           name=Model.get_value(oIter,0)
           if name != self.sNullValue and State[name]:
               self.TreeView.get_selection().select_iter(oIter)
           else:
               self.TreeView.get_selection().unselect_iter(oIter)
           oIter=Model.iter_next(oIter)

    def get_selection(self,selList,State):
        Model,Selection = self.TreeView.get_selection().get_selected_rows()
        for oPath in Selection:
            oIter = Model.get_iter(oPath)
            name = Model.get_value(oIter,0)
            if name!=self.sNullValue:
               State[name]=True
               selList.append(name)

