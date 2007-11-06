"""Generic Scrolled List, used in the Filter Dialo and elsewhere"""
# ScrolledList.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk, gobject
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class ScrolledList(gtk.Frame):
    """Frame containing an auto scrolled list"""
    def __init__(self, sTitle):
        super(ScrolledList, self).__init__(None)
        self._aList = gtk.ListStore(gobject.TYPE_STRING)
        self._oTreeView = gtk.TreeView(self._aList)
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        oMyScroll = AutoScrolledWindow(self._oTreeView)
        self.add(oMyScroll)
        oCell1 = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn(sTitle, oCell1, markup=0)
        self._oTreeView.append_column(oColumn)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    view = property(fget=lambda self: self._oTreeView,
            doc="Associated View Object")
    itemlist = property(fget=lambda self: self._aList, doc="List of values")

    def set_select_single(self):
        """set selection to single mode"""
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def set_select_multiple(self):
        """set selection to multiple mode"""
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    def get_selection(self):
        """Return a list of the selected elements of the list"""
        aSelectedList = []
        oModel, oSelection = self._oTreeView.get_selection().get_selected_rows()
        for oPath in oSelection:
            oIter = oModel.get_iter(oPath)
            sName = oModel.get_value(oIter, 0)
            aSelectedList.append(sName)
        return aSelectedList

    def fill_list(self, aVals):
        """Fill the list store with the given values"""
        self._aList.clear()
        for sEntry in aVals:
            oIter = self._aList.append(None)
            self._aList.set(oIter, 0, sEntry)
