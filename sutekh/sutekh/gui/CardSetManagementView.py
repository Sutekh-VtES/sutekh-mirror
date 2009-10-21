# CardSetManagementView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""gtk.TreeView class the card set list."""

import gtk
from sutekh.gui.CardSetManagementModel import CardSetManagementModel
from sutekh.gui.FilteredView import FilteredView

class CardSetManagementView(FilteredView):
    """Tree View for the card set list."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    def __init__(self, oController, oMainWindow):
        oModel = CardSetManagementModel(oMainWindow)
        oModel.enable_sorting()
        super(CardSetManagementView, self).__init__(oController,
                oMainWindow, oModel, oMainWindow.config_file)

        # Selecting rows
        self.set_select_single()

        # Drag and Drop
        aTargets = [ ('STRING', 0, 0),      # second 0 means TARGET_STRING
                     ('text/plain', 0, 0) ] # and here

        self.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                aTargets, gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.connect('drag_data_get', self.drag_card_set)
        self.connect('row_activated', self._oController.row_clicked)
        self.connect('drag_data_received', self._oController.card_set_drop)

        self.set_name('card set view')
        # Grid Lines

        self.oNameCell = gtk.CellRendererText()
        oColumn = gtk.TreeViewColumn("Card Sets", self.oNameCell, markup=0)
        oColumn.set_expand(True)
        oColumn.set_resizable(True)
        oColumn.set_sort_column_id(0)
        self.append_column(oColumn)
        self._oModel.load()

        self.set_expander_column(oColumn)

    # Introspection

    def drag_card_set(self, _oBtn, _oDragContext, oSelectionData, _oInfo,
            _oTime):
        """Allow card sets to be dragged to a frame."""
        sSetName = self.get_selected_card_set()
        if not sSetName:
            return
        sData = "\n".join(['Card Set:', sSetName])
        oSelectionData.set(oSelectionData.target, 8, sData)

    # pylint: enable-msg=R0913

    def get_selected_card_set(self):
        """Return the currently selected card set name, or None if nothing
           is selected."""
        oModel, aSelectedRows = self._oSelection.get_selected_rows()
        if len(aSelectedRows) != 1:
            # Only feasible when we have a single card set selected
            return None
        oPath = aSelectedRows[0]
        return oModel.get_name_from_path(oPath)

    def get_path_at_pointer(self):
        """Get the path at the current pointer position"""
        iXPos, iYPos, _oIgnore = self.get_bin_window().get_pointer()
        tRes = self.get_path_at_pos(iXPos, iYPos)
        if tRes:
            return tRes[0]
        return None
