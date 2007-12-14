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
        self._oListStore = gtk.ListStore(gobject.TYPE_STRING)
        self._oTreeView = gtk.TreeView(self._oListStore)
        oCell1 = gtk.CellRendererText()
        oColumn1 = gtk.TreeViewColumn(sTitle, oCell1, markup=0)
        self._oTreeView.append_column(oColumn1)
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        oMyScroll = AutoScrolledWindow(self._oTreeView)
        self.add(oMyScroll)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    view = property(fget=lambda self: self._oTreeView,
            doc="Associated View Object")
    itemlist = property(fget=lambda self: self._oListStore, doc="List of values")

    def add_second_column(self, sTitle):
        oCell2 = gtk.CellRendererText()
        oColumn2 = gtk.TreeViewColumn(sTitle, oCell2)
        self._oTreeView.append_column(oColumn2)
        oColumn2.set_cell_data_func(oCell2, self._render_second_column)
        self.dSecondColVals = {}

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

    def set_selected(self, sEntry):
        """Select the current entry"""
        oIter = self._oListStore.get_iter_first()
        while oIter is not None:
            sName = self._oListStore.get_value(oIter, 0)
            if sName == sEntry:
                oPath = self._oListStore.get_path(oIter)
                self._oTreeView.set_cursor(oPath)
                return
            oIter = self._oListStore.iter_next(oIter)

    def fill_list(self, aVals):
        """Fill the list store with the given values"""
        self._oListStore.clear()
        for sEntry in aVals:
            oIter = self._oListStore.append(None)
            self._oListStore.set(oIter, 0, sEntry)

    def fill_second_column(self, dVals):
        self.dSecondColVals = dVals
        self._oTreeView.queue_draw()

    def _render_second_column(self, oColumn, oCell, oModel, oIter):
        sKey = oModel.get_value(oIter, 0)
        if sKey in self.dSecondColVals.keys():
            oCell.set_property("markup", self.dSecondColVals[sKey])
        else:
            oCell.set_property("markup", "")



