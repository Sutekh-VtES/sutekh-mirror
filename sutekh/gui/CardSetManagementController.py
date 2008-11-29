# CardSetManagementController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Controller class the card set list."""

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.CardSetManagementView import CardSetManagementView
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.SutekhDialog import do_complaint_warning, do_complaint
from sutekh.core.CardSetUtilities import delete_physical_card_set, \
        find_children, detect_loop, get_loop_names, break_loop

def split_selection_data(sSelectionData):
    """Helper function to subdivide selection string into bits again"""
    if sSelectionData == '':
        return 'None', ['']
    aLines = sSelectionData.splitlines()
    sSource = aLines[0]
    if sSource == "Sutekh Pane:" or sSource == 'Card Set:':
        return sSource, aLines
    # Irrelevant to us
    return 'None', ['']

def reparent_card_set(oCardSet, oNewParent):
    """Helper function to ensure that reparenting a card set doesn't
       cause loops"""
    if oNewParent:
        # Can only be a problem if the new parent is a card set
        oOldParent = oCardSet.parent
        oCardSet.parent = oNewParent
        oCardSet.syncUpdate()
        if detect_loop(oCardSet):
            oCardSet.parent = oOldParent
            oCardSet.syncUpdate()
            do_complaint('Changing parent of %s to %s introduces a'
                    ' loop. Leaving the parent unchanged.' % (oCardSet.name,
                        oNewParent.name), gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_CLOSE)
        else:
            return True
    else:
        oCardSet.parent = oNewParent
        oCardSet.syncUpdate()
        return True
    return False

def check_ok_to_delete(oCardSet):
    """Check if the user is OK with deleting the card set."""
    aChildren = find_children(oCardSet)
    iResponse = gtk.RESPONSE_OK
    if len(oCardSet.cards) > 0 and len(aChildren) > 0:
        iResponse = do_complaint_warning("Card Set %s Not Empty and"
                " Has Children. Really Delete?" % oCardSet.name)
    elif len(oCardSet.cards) > 0:
        iResponse = do_complaint_warning("Card Set %s Not Empty."
                " Really Delete?" % oCardSet.name)
    elif len(aChildren) > 0:
        iResponse = do_complaint_warning("Card Set %s"
                " Has Children. Really Delete?" % oCardSet.name)
    return iResponse == gtk.RESPONSE_OK

def update_card_set(oCardSet, oEditDialog, oMainWindow, oMenu):
    """Update the details of the card set when the user edits them."""
    sOldName = oCardSet.name
    sName = oEditDialog.get_name()
    if sName != sOldName:
        oCardSet.name = sName
        oMainWindow.rename_pane(sOldName, sName)
    oCardSet.author = oEditDialog.get_author()
    oCardSet.comment = oEditDialog.get_comment()
    oCardSet.annotations = oEditDialog.get_annotations()
    oParent = oEditDialog.get_parent()
    if oParent != oCardSet.parent:
        reparent_card_set(oCardSet, oParent)
    oCardSet.syncUpdate()
    # Update frame menu
    if oMenu:
        oMenu.update_card_set_menu(oCardSet)
    oMainWindow.reload_pcs_list()

class CardSetManagementController(object):
    """Controller object for the card set list."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    def __init__(self, oMainWindow, oFrame):
        self._oMainWindow = oMainWindow
        self._oFrame = oFrame
        self._oFilterDialog = None
        # Check the current set for loops
        for oCS in PhysicalCardSet.select():
            if detect_loop(oCS):
                sLoop = "->".join(get_loop_names(oCS))
                sBreakName = break_loop(oCS)
                do_complaint(
                        'Loop %s in the card sets relationships.\n'
                        'Breaking at %s' % (sLoop, sBreakName),
                        gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE)
                # We break the loop, and let the user fix things,
                # rather than try and be too clever
        self._oView = CardSetManagementView(oMainWindow, self)
        self._oModel = self._oView.get_model()

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    view = property(fget=lambda self: self._oView, doc="Associated View")
    model = property(fget=lambda self: self._oModel, doc="View's Model")
    frame = property(fget=lambda self: self._oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    # pylint: disable-msg=W0613
    # oWidget, oMenuItem required by function signature
    def get_filter(self, oMenuItem):
        """Get the Filter from the FilterDialog."""
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWindow,
                    self._oMainWindow.config_file, 'PhysicalCardSet')

        self._oFilterDialog.run()

        if self._oFilterDialog.was_cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.get_filter()
        if oFilter != None:
            self._oModel.selectfilter = oFilter
            if not self._oModel.applyfilter:
                # If a filter is set, automatically apply
                oMenuItem.set_apply_filter(True)
            else:
                # Filter Changed, so reload
                self._oModel.load()
        else:
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if self._oModel.applyfilter:
                oMenuItem.set_apply_filter(False)
            else:
                self._oModel.load()

    def run_filter(self, bState):
        """Enable or diable the current filter based on bState"""
        if self._oModel.applyfilter != bState:
            self._oModel.applyfilter = bState
            self._oModel.load()

    def create_new_card_set(self, oWidget):
        """Create a new card set"""
        oDialog = CreateCardSetDialog(self._oMainWindow)
        oDialog.run()
        sName = oDialog.get_name()
        # pylint: disable-msg=E1102, W0612
        # W0612 - oCS isn't important, as the creation of the new card
        # set is what matters
        if sName:
            sAuthor = oDialog.get_author()
            sComment = oDialog.get_comment()
            oParent = oDialog.get_parent()
            oCS = PhysicalCardSet(name=sName, author=sAuthor,
                    comment=sComment, parent=oParent)
            self._oMainWindow.add_new_physical_card_set(sName)

    def edit_card_set_properties(self, oWidget):
        """Create a new card set"""
        sSetName = self._oView.get_selected_card_set()
        if not sSetName:
            return
        oFrame = self._oMainWindow.find_pane_by_name(sSetName)
        if oFrame:
            oMenu = oFrame.menu
        else:
            oMenu = None
        oCardSet = IPhysicalCardSet(sSetName)
        oDialog = CreateCardSetDialog(self._oMainWindow, oCardSet=oCardSet)
        oDialog.run()
        sName = oDialog.get_name()
        if sName:
            if oFrame and sName != oFrame.view.sSetName:
                oFrame.view.update_name(sName)
            update_card_set(oCardSet, oDialog, self._oMainWindow,
                    oMenu)

    def delete_card_set(self, oWidget):
        """Delete the selected card set."""
        sSetName = self._oView.get_selected_card_set()
        if not sSetName:
            return
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        try:
            oCS = PhysicalCardSet.byName(sSetName)
        except SQLObjectNotFound:
            return
        # Check for card sets this is a parent of
        if check_ok_to_delete(oCS):
            sFrameName = sSetName
            delete_physical_card_set(sSetName)
            self._oMainWindow.remove_frame_by_name(sFrameName)
            self.reload_keep_expanded(False)

    def toggle_in_use_flag(self, oMenuItem):
        """Toggle the in-use status of the card set"""
        sSetName = self._oView.get_selected_card_set()
        if not sSetName:
            return
        try:
            # pylint: disable-msg=E1101
            # SQLObject confuses pylint
            oCS = PhysicalCardSet.byName(sSetName)
        except SQLObjectNotFound:
            return
        oCS.inuse = not oCS.inuse
        oCS.syncUpdate()
        self.reload_keep_expanded(True)

    def row_clicked(self, oTreeView, oPath, oColumn):
        """Handle row clicked events.

           allow double clicks to open a card set.
           """
        sName = self._oModel.get_name_from_path(oPath)
        # check if card set is open before opening again
        oPane = self._oMainWindow.find_pane_by_name(sName)
        if oPane is not None:
            return # Already open, so do nothing
        self._oMainWindow.add_new_physical_card_set(sName)

    def reload_keep_expanded(self, bRestoreSelection):
        """Reload with current expanded state.

           Attempt to reload the card list, keeping the existing structure
           of expanded rows.
           """
        # Internal helper functions
        # See what's expanded
        # pylint: disable-msg=W0612
        # we're not interested in oModel here
        oSelection = self._oView.get_selection()
        if oSelection is not None:
            oModel, aSelectedRows = oSelection.get_selected_rows()
        else:
            aSelectedRows = []
        if len(aSelectedRows) > 0:
            oSelPath = aSelectedRows[0]
        else:
            oSelPath = None
        dExpandedDict = {}
        self._oModel.foreach(self._oView.get_row_status, dExpandedDict)
        # Reload, but use cached info
        self._oModel.load()
        # Re-expand stuff
        self._oView.set_row_status(dExpandedDict)
        if oSelPath and bRestoreSelection:
            # Restore selection
            oSelection.select_path(oSelPath)
        # Handle any defferred database single issues
        self._oMainWindow.do_all_queued_reloads()

    # pylint: disable-msg=R0913
    # arguments as required by function signature
    def card_set_drop(self, oWdgt, oContext, iXPos, iYPos, oData, oInfo,
            oTime):
        """Default drag-n-drop handler."""
        # Pass off to the Frame Handler
        sSource, aData = split_selection_data(oData.data)
        if sSource == "Sutekh Pane:":
            self._oFrame.drag_drop_handler(oWdgt, oContext, iXPos, iYPos,
                    oData, oInfo, oTime)
        elif sSource == "Card Set:":
            # Find the card set at iXPos, iYPos
            # Need to do this to skip avoid headers and such confusing us
            oPath = self._oView.get_path_at_pointer()
            if oPath:
                sTargetName = self._oModel.get_name_from_path(oPath)
                sThisName = aData[1]
                # pylint: disable-msg=W0704
                # doing nothing on SQLObjectNotFound seems the best choice
                try:
                    oDraggedCS = IPhysicalCardSet(sThisName)
                    oParentCS = IPhysicalCardSet(sTargetName)
                    if reparent_card_set(oDraggedCS, oParentCS):
                        self.reload_keep_expanded(False)
                        oPath = self._oModel.get_path_from_name(sThisName)
                        # Make newly dragged set visible
                        if oPath:
                            self._oView.expand_to_path(oPath)
                        oContext.finish(True, False, oTime)
                except SQLObjectNotFound:
                    pass
        oContext.finish(False, False, oTime)

    # pylint: enable-msg=R0913
