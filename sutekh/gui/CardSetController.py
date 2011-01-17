# CardSetController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Controller for the card sets"""

from sqlobject import SQLObjectNotFound
from sutekh.gui.GuiCardSetFunctions import check_ok_to_delete, \
        update_card_set
from sutekh.gui.CardSetView import CardSetView
from sutekh.core.DBSignals import send_changed_signal
from sutekh.core.SutekhObjects import IPhysicalCardSet, PhysicalCardSet, \
        IAbstractCard, PhysicalCard, MapPhysicalCardToPhysicalCardSet, \
        IExpansion, IPhysicalCard
from sutekh.core.CardSetUtilities import delete_physical_card_set


class CardSetController(object):
    """Controller class for the Card Sets."""
    _sFilterType = 'PhysicalCard'

    def __init__(self, sName, oMainWindow, oFrame, bStartEditable):
        # pylint: disable-msg=E1101, E1103
        # SQLObject methods confuse pylint
        self._oMainWindow = oMainWindow
        self._oMenu = None
        self._oFrame = oFrame
        self._oView = CardSetView(oMainWindow, self, sName, bStartEditable)
        self.__oPhysCardSet = IPhysicalCardSet(sName)
        self.model.set_controller(self)

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    view = property(fget=lambda self: self._oView, doc="Associated View")
    model = property(fget=lambda self: self._oView._oModel, doc="View's Model")
    frame = property(fget=lambda self: self._oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def cleanup(self):
        """Remove the signal handlers."""
        self.model.cleanup()

    def set_card_text(self, oCard):
        """Set card text to reflect selected card."""
        self._oMainWindow.set_card_text(oCard)

    def inc_card(self, oPhysCard, sCardSetName):
        """Returns True if a card was successfully added, False otherwise."""
        return self.add_card(oPhysCard, sCardSetName)

    def dec_card(self, oPhysCard, sCardSetName):
        """Returns True if a card was successfully removed, False otherwise."""
        # pylint: disable-msg=E1101, E1103
        # SQLObject +Pyprotocol methods confuse pylint
        try:
            if sCardSetName:
                oThePCS = IPhysicalCardSet(sCardSetName)
            else:
                oThePCS = self.__oPhysCardSet
            # find if the physical card given is in the set
            # Can only happen when expansion is None, since that may be a
            # top-level item or an expansion level item.
            # This also means, when removing cards from via a top-level item,
            # we will prefer removing cards without expansion information if
            # they are present.
            if not oPhysCard.expansion and \
                    MapPhysicalCardToPhysicalCardSet.selectBy(
                            physicalCardID=oPhysCard.id,
                            physicalCardSetID=oThePCS.id).count() == 0:
                # Given card is not in the card set, so consider all
                # cards with the same name.
                aPhysCards = list(PhysicalCard.selectBy(
                    abstractCardID=oPhysCard.abstractCard.id))
            else:
                aPhysCards = [oPhysCard]
        except SQLObjectNotFound:
            # Bail on error
            return False

        for oCard in aPhysCards:
            # Need to remove a single physical card from the mapping table
            # Can't use PhysicalCardSet.remove, as that removes all the cards
            aCandCards = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id,
                    physicalCardSetID=oThePCS.id))
            if len(aCandCards) > 0:
                # Found candidates, so remove last one
                MapPhysicalCardToPhysicalCardSet.delete(aCandCards[-1].id)
                oThePCS.syncUpdate()
                # signal to update the model
                send_changed_signal(oThePCS, oCard, -1)
                return True
        # Got here, so we failed to remove a card
        return False

    def add_card(self, oPhysCard, sCardSetName):
        """Returns True if a card was successfully added, False otherwise."""
        # pylint: disable-msg=E1101, E1103
        # SQLObject + PyProtocols methods confuse pylint
        try:
            if sCardSetName:
                oThePCS = IPhysicalCardSet(sCardSetName)
            else:
                oThePCS = self.__oPhysCardSet
        except SQLObjectNotFound:
            # Any error means we bail
            return False

        oThePCS.addPhysicalCard(oPhysCard.id)
        oThePCS.syncUpdate()
        # Signal to update the model
        send_changed_signal(oThePCS, oPhysCard, 1)
        return True

    def edit_properties(self, _oMenuWidget):
        """Run the dialog to update the card set properties"""
        update_card_set(self.__oPhysCardSet, self._oMainWindow)

    def update_to_new_db(self):
        """Update the internal card set to the new DB."""
        try:
            # cardset id -> profile map should have been updated before we
            # get here
            self.__oPhysCardSet = IPhysicalCardSet(self.view.sSetName)
            self.model.update_to_new_db(self.view.sSetName)
        except SQLObjectNotFound:
            # No longer in the database, so remove from the window
            self._oFrame.close_frame()

    def delete_card_set(self):
        """Delete this card set from the database."""
        # Check if CardSet is empty
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        if check_ok_to_delete(self.__oPhysCardSet):
            self._oMainWindow.config_file.clear_cardset_profile(
                    self.model.cardset_id)  # Remove profile entry
            # Card Set is being deleted, so close pane
            self._oFrame.close_frame()
            # Close any other open copies as well
            for oFrame in self._oMainWindow.find_cs_pane_by_set_name(
                    self.view.sSetName):
                oFrame.close_frame()
            # Tell window to clean up
            delete_physical_card_set(self.view.sSetName)
            self._oMainWindow.reload_pcs_list()

    def save_iter_state(self, aIters):
        """Ask the view to save the state for us"""
        dStates = {}
        self.view.save_iter_state(aIters, dStates)
        return dStates

    def restore_iter_state(self, aIters, dStates):
        """Ask the view to restore the state"""
        self.view.restore_iter_state(aIters, dStates)

    def _get_card(self, sCardName, sExpansionName):
        """Convert card name & Expansion to PhsicalCard.

           Help for add_paste_data."""
        oExp = None
        try:
            if sExpansionName and sExpansionName != 'None' and \
                    sExpansionName != self.model.sUnknownExpansion:
                oExp = IExpansion(sExpansionName)
            oAbsCard = IAbstractCard(sCardName)
            oPhysCard = IPhysicalCard((oAbsCard, oExp))
            return oPhysCard
        except SQLObjectNotFound:
            # Error, so bail
            return None

    def add_paste_data(self, sSource, aCards):
        """Helper function for drag+drop and copy+paste.

           Only works when we're editable.
           """
        aSources = sSource.split(':')
        if not self.model.bEditable:
            return False
        if aSources[0] in ("Phys", PhysicalCardSet.sqlmeta.table):
            # Add the cards, Count Matters
            for iCount, sCardName, sExpansion in aCards:
                # Use None to indicate this card set
                oPhysCard = self._get_card(sCardName, sExpansion)
                if not oPhysCard:
                    # error, so skip this. (Warn user?)
                    continue
                if aSources[0] == "Phys":
                    # Only ever add 1 when dragging from physical card list
                    self.add_card(oPhysCard, None)
                else:
                    for _iLoop in range(iCount):
                        self.add_card(oPhysCard, None)
            return True
        else:
            return False

    def change_selected_card_count(self, dSelectedData):
        """Helper function to set the selected cards to the specified number"""
        for oPhysCard in dSelectedData:
            for sCardSetName, (iCardCount, iNewCnt) in \
                    dSelectedData[oPhysCard].iteritems():
                if iNewCnt < iCardCount:
                    # remove cards
                    for _iAttempt in range(iCardCount - iNewCnt):
                        # None as card set indicates this card set
                        self.dec_card(oPhysCard, sCardSetName)
                elif iNewCnt > iCardCount:
                    # add cards
                    for _iAttempt in range(iNewCnt - iCardCount):
                        self.inc_card(oPhysCard, sCardSetName)
