# ScrolledList.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Generic Scrolled List, used in the Filter Dialo and elsewhere"""

import gtk, gobject
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class ScrolledList(gtk.Frame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Frame containing an auto scrolled list"""
    def __init__(self, sTitle):
        super(ScrolledList, self).__init__(None)
        self._oListStore = gtk.ListStore(gobject.TYPE_STRING)
        self._oTreeView = gtk.TreeView(self._oListStore)
        oCell1 = gtk.CellRendererText()
        oColumn1 = gtk.TreeViewColumn(sTitle, oCell1, markup=0)
        self.dSecondColVals = {}
        self._oTreeView.append_column(oColumn1)
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        oMyScroll = AutoScrolledWindow(self._oTreeView)
        self.add(oMyScroll)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    # pylint: disable-msg=W0212
    # allow access via these properties
    view = property(fget=lambda self: self._oTreeView,
            doc="Associated View Object")
    itemlist = property(fget=lambda self: self._oListStore,
            doc="List of values")
    # disable-msg=W0212

    def add_second_column(self, sTitle):
        """Add an extra column to the list."""
        oCell2 = gtk.CellRendererText()
        oColumn2 = gtk.TreeViewColumn(sTitle, oCell2)
        self._oTreeView.append_column(oColumn2)
        oColumn2.set_cell_data_func(oCell2, self._render_second_column)

    def set_select_single(self):
        """set selection to single mode"""
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def set_select_multiple(self):
        """set selection to multiple mode"""
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

    def set_select_none(self):
        """set selection mode to none"""
        self._oTreeView.get_selection().set_mode(gtk.SELECTION_NONE)

    def get_selection(self):
        """Return a list of the selected elements of the list"""
        aSelectedList = []
        oModel, oSelection = \
                self._oTreeView.get_selection().get_selected_rows()
        for oPath in oSelection:
            oIter = oModel.get_iter(oPath)
            sName = oModel.get_value(oIter, 0)
            aSelectedList.append(sName)
        return aSelectedList

    def set_selection(self, aRowsToSelect):
        """Set the selected rows to aRowsToSelect."""
        aRowsToSelect = set(aRowsToSelect)
        oIter = self._oListStore.get_iter_first()
        oTreeSelection = self._oTreeView.get_selection()
        oTreeSelection.unselect_all()
        while oIter is not None:
            sName = self._oListStore.get_value(oIter, 0)
            if sName in aRowsToSelect:
                oTreeSelection.select_iter(oIter)
            oIter = self._oListStore.iter_next(oIter)

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
        """Fill the values in the second column."""
        self.dSecondColVals = dVals
        self._oTreeView.queue_draw()

    # pylint: disable-msg=W0613
    # oColumn required by function signature
    def _render_second_column(self, oColumn, oCell, oModel, oIter):
        """Method to render the values in the second column."""
        sKey = oModel.get_value(oIter, 0)
        if sKey in self.dSecondColVals:
            oCell.set_property("markup", self.dSecondColVals[sKey])
        else:
            oCell.set_property("markup", "")



