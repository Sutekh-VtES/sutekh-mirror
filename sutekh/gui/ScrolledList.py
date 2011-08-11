# ScrolledList.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Generic Scrolled List, used in the Filter Dialog and elsewhere"""

import gtk
import gobject
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CustomDragIconView import CustomDragIconView


class ScrolledListStore(gtk.ListStore):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Simple list store for ScrolledList widget"""
    def __init__(self):
        super(ScrolledListStore, self).__init__(gobject.TYPE_STRING)

    def fill_list(self, aVals):
        """Fill the list"""
        self.clear()
        for sEntry in aVals:
            oIter = self.append(None)
            self.set(oIter, 0, sEntry)


class ScrolledListView(CustomDragIconView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Simple tree view for the ScrolledList widget"""
    def __init__(self, sTitle, oModel=None, bSpecialSelect=False):
        if not oModel:
            oModel = ScrolledListStore()
        super(ScrolledListView, self).__init__(oModel)
        oCell1 = gtk.CellRendererText()
        oColumn1 = gtk.TreeViewColumn(sTitle, oCell1, markup=0)
        self.append_column(oColumn1)
        self._oSelection.set_mode(gtk.SELECTION_MULTIPLE)

        if bSpecialSelect:
            self._oSelection.connect('changed', self.row_selected)

    # pylint: disable-msg=W0212
    # allow access via these properties
    store = property(fget=lambda self: self._oModel, doc="List of values")
    # disable-msg=W0212

    def get_selected_data(self):
        """Get the list of selected values"""
        aSelectedList = []
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        for oPath in aSelectedRows:
            oIter = oModel.get_iter(oPath)
            sName = oModel.get_value(oIter, 0)
            aSelectedList.append(sName)
        return aSelectedList

    def set_selected_rows(self, aRowsToSelect):
        """Set the selection to the correct list"""
        aRowsToSelect = set(aRowsToSelect)
        oIter = self._oModel.get_iter_first()
        self._oSelection.unselect_all()
        while oIter is not None:
            sName = self._oModel.get_value(oIter, 0)
            if sName in aRowsToSelect:
                self._oSelection.select_iter(oIter)
            oIter = self._oModel.iter_next(oIter)

    def set_selected_entry(self, sEntry):
        """Set the selection to the correct entry"""
        oIter = self._oModel.get_iter_first()
        while oIter is not None:
            sName = self._oModel.get_value(oIter, 0)
            if sName == sEntry:
                oPath = self._oModel.get_path(oIter)
                self.set_cursor(oPath)
                return
            oIter = self._oModel.iter_next(oIter)


class ScrolledList(gtk.Frame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Frame containing an auto scrolled list"""
    def __init__(self, sTitle, oModel=None, bSpecialSelect=None):
        super(ScrolledList, self).__init__(None)
        self._oTreeView = ScrolledListView(sTitle, oModel, bSpecialSelect)
        oMyScroll = AutoScrolledWindow(self._oTreeView)
        self.add(oMyScroll)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    # pylint: disable-msg=W0212
    # allow access via these properties
    view = property(fget=lambda self: self._oTreeView,
            doc="Associated View Object")
    # disable-msg=W0212

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
        return self._oTreeView.get_selected_data()

    def set_selected_rows(self, aRowsToSelect):
        """Set the selected rows to aRowsToSelect."""
        self._oTreeView.set_selected_rows(aRowsToSelect)

    def set_selected_entry(self, sEntry):
        """Select the current entry"""
        self._oTreeView.set_selected_entry(sEntry)

    def fill_list(self, aVals):
        """Fill the list store with the given values"""
        self._oTreeView.store.fill_list(aVals)

    def get_selection_object(self):
        """Get a reference to the TreeView selection"""
        return self._oTreeView.get_selection()
