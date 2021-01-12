# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Generic Scrolled List, used in the Filter Dialog and elsewhere"""

from gi.repository import Gtk, GObject

from .AutoScrolledWindow import AutoScrolledWindow
from .CustomDragIconView import CustomDragIconView


class ScrolledListStore(Gtk.ListStore):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Simple list store for ScrolledList widget"""
    def __init__(self):
        super().__init__(GObject.TYPE_STRING)

    def fill_list(self, aVals):
        """Fill the list"""
        self.clear()
        for sEntry in aVals:
            oIter = self.append(None)
            self.set(oIter, 0, sEntry)


class ScrolledListView(CustomDragIconView):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Simple tree view for the ScrolledList widget"""
    def __init__(self, sTitle, oModel=None, bSpecialSelect=False):
        if not oModel:
            oModel = ScrolledListStore()
        super().__init__(oModel)
        oCell1 = Gtk.CellRendererText()
        oColumn1 = Gtk.TreeViewColumn(sTitle, oCell1, markup=0)
        self.append_column(oColumn1)
        self._oSelection.set_mode(Gtk.SelectionMode.MULTIPLE)

        if bSpecialSelect:
            self._oSelection.connect('changed', self.row_selected)

    # pylint: disable=protected-access
    # allow access via these properties
    store = property(fget=lambda self: self._oModel, doc="List of values")
    # pylint: enable=protected-access

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


class ScrolledList(Gtk.Frame):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Frame containing an auto scrolled list"""
    def __init__(self, sTitle, oModel=None, bSpecialSelect=None):
        super().__init__()
        self._oTreeView = ScrolledListView(sTitle, oModel, bSpecialSelect)
        oMyScroll = AutoScrolledWindow(self._oTreeView)
        self.add(oMyScroll)
        self.set_shadow_type(Gtk.ShadowType.NONE)
        self.show_all()

    # pylint: disable=protected-access
    # allow access via these properties
    view = property(fget=lambda self: self._oTreeView,
                    doc="Associated View Object")
    # pylint: enable=protected-access

    def set_select_single(self):
        """set selection to single mode"""
        self._oTreeView.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

    def set_select_multiple(self):
        """set selection to multiple mode"""
        self._oTreeView.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

    def set_select_none(self):
        """set selection mode to none"""
        self._oTreeView.get_selection().set_mode(Gtk.SelectionMode.NONE)

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
