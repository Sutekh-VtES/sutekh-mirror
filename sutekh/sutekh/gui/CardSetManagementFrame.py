# CardSetManagementFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Window for Managing Physical and Abstract Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Pane for a list of card sets"""

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.SutekhUtility import delete_physical_card_set
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.Filters import NullFilter
from sutekh.gui.SutekhDialog import do_complaint_error, do_complaint_warning
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.CardSetManagementMenu import CardSetManagementMenu
from sutekh.gui.CardSetManagementView import CardSetManagementView
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class CardSetManagementFrame(BasicFrame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    """Pane for the List of card sets.

       Provides the actions associated with this Pane - creating new
       card sets, filtering, etc.
       """
    _sFilterType = 'PhysicalCardSet'
    _sName = 'Physical Card Set List'
    _oSetClass = PhysicalCardSet

    def __init__(self, oMainWindow):
        super(CardSetManagementFrame, self).__init__(oMainWindow)
        self._oFilter = NullFilter()
        self._oFilterDialog = None
        self._oMenu = None
        self._oView = CardSetManagementView(oMainWindow)
        self.set_name("physical card sets list")
        self.add_parts()

    # pylint: disable-msg=W0212
    # We allow access via these properties
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    # pylint: enable-msg=W0212

    def add_parts(self):
        """Add a list object to the frame"""
        oMbox = gtk.VBox(False, 2)

        self.set_title(self._sName)
        oMbox.pack_start(self._oTitle, False, False)

        self._oMenu = CardSetManagementMenu(self, self._oMainWindow,
                self._sName)

        oMbox.pack_start(self._oMenu, False, False)

        self._oView.connect('row_activated', self.row_clicked)

        oMbox.pack_start(AutoScrolledWindow(self._oView), expand=True)

        # allow dragging card sets from the list
        self._oView.drag_source_set(
                gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK, self.aDragTargets,
                gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self._oView.connect('drag-data-get', self.drag_card_set)
        # setup default targets
        self.set_drag_handler()

        self.add(oMbox)
        self.show_all()

    # pylint: disable-msg=W0613, R0913
    # arguments required by function signature
    def drag_card_set(self, oBtn, oDragContext, oSelectionData, oInfo, oTime):
        """Allow card sets to be dragged to a frame."""
        aSelection = self._oScrolledList.get_selection()
        if len(aSelection) != 1:
            return
        # Don't respond to the dragging of an already open card set, and so on
        sSetName = aSelection[0]
        sPrefix = 'PCS:'
        sFrameName = sSetName
        if sFrameName in self._oMainWindow.dOpenFrames.values():
            return
        sData = "\n".join(['Sutekh Pane:', 'Card Set Pane:', sPrefix,
            sSetName])
        oSelectionData.set(oSelectionData.target, 8, sData)

    def create_new_card_set(self, oWidget):
        """Create a new card set"""
        oDialog = CreateCardSetDialog(self._oMainWindow, 'Physical')
        fOpenCardSet = self._oMainWindow.add_new_physical_card_set
        oDialog.run()
        (sName, sAuthor, sDescription) = oDialog.get_data()
        oDialog.destroy()
        # pylint: disable-msg=E1102, W0612
        # W0612 - oCS isn't important, as the creation of the new card
        # set is what matters
        if sName is not None:
            iCnt = PhysicalCardSet.selectBy(name=sName).count()
            if iCnt > 0:
                do_complaint_error("Chosen Card Set Name is already in use.")
            else:
                oCS = PhysicalCardSet(name=sName, author=sAuthor,
                        comment=sDescription)
                fOpenCardSet(sName)

    def delete_card_set(self, oWidget):
        """Delete the selected card set."""
        aSelection = self._oScrolledList.get_selection()
        if len(aSelection) != 1:
            return
        else:
            sSetName = aSelection[0]
        try:
            oCS = PhysicalCardSet.byName(sSetName)
        except SQLObjectNotFound:
            return
        if len(oCS.cards) > 0:
            iResponse = do_complaint_warning("Card Set %s Not Empty. Really"
                    " Delete?" % sSetName)
            if iResponse == gtk.RESPONSE_CANCEL:
                # Don't delete
                return
        # Got here, so delete the card set
        sFrameName = sSetName
        delete_physical_card_set(sSetName)
        self._oMainWindow.remove_frame_by_name(sFrameName)

    def set_filter(self):
        """Set the filter applied to the list."""
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWindow,
                    self._oMainWindow.config_file, self._sFilterType)
        self._oFilterDialog.run()

        if self._oFilterDialog.was_cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.get_filter()
        if oFilter != None:
            self._oFilter = oFilter
            if self._oMenu.get_apply_filter():
                self.reload()
            else:
                # Let toggle reload for us
                self._oMenu.set_apply_filter(True)
        else:
            self._oFilter = NullFilter()
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if not self._oMenu.get_apply_filter():
                self.reload()
            else:
                # Let toggle reload for us
                self._oMenu.set_apply_filter(False)

    def row_clicked(self, oTreeView, oPath, oColumn):
        """Handle row clicked events.

           allow double clicks to open a card set.
           """
        oModel = oTreeView.get_model()
        # We are pointing to a ListStore, so the iters should always be valid
        # Need to dereference to the actual path though, as iters not unique
        oIter = oModel.get_iter(oPath)
        sName = oModel.get_value(oIter, 0)
        # check if card set is open before opening again
        sFrameName = sName
        oPane = self._oMainWindow.find_pane_by_name(sFrameName)
        if oPane is not None:
            return # Already open, so do nothing
        oFrame = self._oMainWindow.add_pane_end()
        self._oMainWindow.replace_with_physical_card_set(sName, oFrame)

    # pylint: enable-msg=W0613, R0913

    # pylint: disable-msg=W0613
    # oMenuItem required by function signature
    def toggle_in_use_flag(self, oMenuItem):
        """Toggle the in-use status of the card set"""
        aSelection = self._oView.get_selection()
        if len(aSelection) != 1:
            return
        else:
            sSetName = aSelection[0]
        try:
            # pylint: disable-msg=E1101
            # SQLObject confuses pylint
            oCS = PhysicalCardSet.byName(sSetName)
        except SQLObjectNotFound:
            return
        oCS.inuse = not oCS.inuse
        oCS.syncUpdate()
        self.reload()
        # Restore selection
        self._oView.set_selected(oCS.name)
