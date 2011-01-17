# CardSetManagementController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Controller class the card set list."""

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet
from sutekh.gui.CardSetManagementView import CardSetManagementView
from sutekh.core.CardSetUtilities import delete_physical_card_set
from sutekh.gui.GuiCardSetFunctions import create_card_set, update_card_set, \
        check_ok_to_delete, break_existing_loops


class CardSetManagementController(object):
    """Controller object for the card set list."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    _sFilterType = 'PhysicalCardSet'

    def __init__(self, oMainWindow, oFrame):
        self._oMainWindow = oMainWindow
        self._oFrame = oFrame
        # Check the current set for loops
        break_existing_loops()
        self._oView = CardSetManagementView(self, oMainWindow)
        self._oModel = self._oView.get_model()

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    view = property(fget=lambda self: self._oView, doc="Associated View")
    model = property(fget=lambda self: self._oModel, doc="View's Model")
    frame = property(fget=lambda self: self._oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def create_new_card_set(self, _oWidget):
        """Create a new card set"""
        sName = create_card_set(self._oMainWindow)
        if sName:
            self._oMainWindow.add_new_physical_card_set(sName, True)

    def edit_card_set_properties(self, _oWidget):
        """Create a new card set"""
        sSetName = self._oView.get_selected_card_set()
        if not sSetName:
            return
        oCardSet = IPhysicalCardSet(sSetName)
        update_card_set(oCardSet, self._oMainWindow)

    def delete_card_set(self, _oWidget):
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
            for oFrame in self._oMainWindow.find_cs_pane_by_set_name(sSetName):
                oFrame.close_frame()
            self._oMainWindow.config_file.clear_cardset_profile(
                    'cs%d' % oCS.id)
            delete_physical_card_set(sSetName)
            self.view.reload_keep_expanded(False)

    def toggle_in_use_flag(self, _oMenuWidget):
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
        self.view.reload_keep_expanded(True)
