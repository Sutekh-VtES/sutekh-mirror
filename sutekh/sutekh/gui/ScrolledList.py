# ScrolledList.py
# Scrolled List, used in the Filter Dialo and elsewhere
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
from SutekhObjects import *
from AutoScrolledWindow import AutoScrolledWindow

class ScrolledList(gtk.Frame):
    def __init__(self,title):
        super(ScrolledList,self).__init__(None)
        self.List=gtk.ListStore(gobject.TYPE_STRING)
        self.TreeView=gtk.TreeView(self.List)
        self.TreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        myScroll=AutoScrolledWindow(self.TreeView)
        self.add(myScroll)
        oCell1=gtk.CellRendererText()
        oColumn=gtk.TreeViewColumn(title,oCell1,text=0)
        self.List.append(None) # Create empty items at top of list
        self.TreeView.append_column(oColumn)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    def get_list(self):
        return self.List

    def get_view(self):
        return self.TreeView

    def reset(self,State):
        Model=self.TreeView.get_model()
        oIter=Model.get_iter_first()
        while oIter != None:
           name=Model.get_value(oIter,0)
           if name != None and State[name]:
               self.TreeView.get_selection().select_iter(oIter)
           else:
               self.TreeView.get_selection().unselect_iter(oIter)
           oIter=Model.iter_next(oIter)

    def get_selection(self,selList,State):
        Model,Selection = self.TreeView.get_selection().get_selected_rows()
        for oPath in Selection:
            oIter = Model.get_iter(oPath)
            name = Model.get_value(oIter,0)
            if name!=None:
               State[name]=True
               selList.append(name)

