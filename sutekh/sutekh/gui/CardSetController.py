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
from sutekh.core.DBSignals import listen_row_destroy, listen_row_update, \
        send_changed_signal, disconnect_row_destroy, disconnect_row_update
from sutekh.core.SutekhObjects import IPhysicalCardSet, PhysicalCardSet, \
        IAbstractCard, PhysicalCard, MapPhysicalCardToPhysicalCardSet, \
        IExpansion, IPhysicalCard
from sutekh.core.CardSetUtilities import delete_physical_card_set

class CardSetController(object):
    """Controller class for the Card Sets."""
    _sFilterType = 'PhysicalCard'

    def __init__(self, sName, oMainWindow, oFrame):
        # pylint: disable-msg=E1101, E1103
        # SQLObject methods confuse pylint
        self._oMainWindow = oMainWindow
        self._oMenu = None
        self._oFrame = oFrame
        self._oView = CardSetView(oMainWindow, self, sName)
        self.__oPhysCardSet = IPhysicalCardSet(sName)
        # listen on card set signals
        # We listen here, rather than in the model (as for card set changes),
        # to use queue_reload to delay processing until after the database
        listen_row_update(self.card_set_changed, PhysicalCardSet)
        listen_row_destroy(self.card_set_deleted, PhysicalCardSet)
        # We don't listen for card set creation, since newly created card
        # sets aren't inuse. If that changes, we'll need to add an additional
        # signal listen here
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
        disconnect_row_update(self.card_set_changed, PhysicalCardSet)
        disconnect_row_destroy(self.card_set_deleted, PhysicalCardSet)
        self.model.cleanup()

    def card_set_changed(self, oCardSet, dChanges):
        """When changes happen that may effect this card set, reload.

           Cases are:
             * when the parent changes
             * when a child card set is added or removed while marked in use
             * when a child card set is marked/unmarked as in use.
             * when a 'sibling' card set is marked/unmarked as in use
             * when a 'sibling' card set is added or removed while marked in
               use
           Whether this requires a reload depends on the current model mode.
           When the parent changes to or from none, we also update the menus
           and the parent card shown view.
           """
        # pylint: disable-msg=E1101, E1103
        # Pyprotocols confuses pylint
        if oCardSet.id == self.__oPhysCardSet.id and \
                dChanges.has_key('parentID'):
            # This card set's parent is changing
            if self.model.changes_with_parent():
                # Parent count is shown, or not shown becuase parent is
                # changing to None, so this affects the shown cards.
                self._oFrame.queue_reload()
        elif oCardSet.parent and oCardSet.parent.id == self.__oPhysCardSet.id \
                and self.model.changes_with_children():
            # This is a child card set, and this can require a reload
            if dChanges.has_key('inuse'):
                # inuse flag being toggled
                self._oFrame.queue_reload()
            elif dChanges.has_key('parentID') and oCardSet.inuse:
                # Inuse card set is being reparented
                self._oFrame.queue_reload()
        elif dChanges.has_key('parentID') and \
                dChanges['parentID'] == self.__oPhysCardSet.id and \
                oCardSet.inuse and self.model.changes_with_children():
            # acquiring a new inuse child card set
            self._oFrame.queue_reload()
        elif self.__oPhysCardSet.parent and self.model.changes_with_siblings():
            # Sibling's are possible, so check for them
            if dChanges.has_key('ParentID') and oCardSet.inuse:
                # Possibling acquiring or losing inuse sibling
                if (dChanges['ParentID'] == self.__oPhysCardSet.parent.id) or \
                        (oCardSet.parent and oCardSet.parent.id ==
                                self.__oPhysCardSet.parent.id):
                    # Reload if needed
                    self._oFrame.queue_reload()
            elif dChanges.has_key('inuse') and oCardSet.parent and \
                    oCardSet.parent.id == self.__oPhysCardSet.parent.id:
                # changing inuse status of sibling
                self._oFrame.queue_reload()

    # _fPostFuncs is passed by SQLObject 0.10, but not by 0.9, so we need to
    # sipport both
    def card_set_deleted(self, oCardSet, _fPostFuncs=None):
        """Listen for card set removal events.

           Needed if child card sets are deleted, for instance.
           """
        # pylint: disable-msg=E1101, E1103
        # Pyprotocols confuses pylint
        if oCardSet.parent and oCardSet.parent.id == \
                self.__oPhysCardSet.id and oCardSet.inuse and \
                self.model.changes_with_children():
            # inuse child card set going, so we need to reload
            self._oFrame.queue_reload()
        if self.__oPhysCardSet.parent and self.model.changes_with_siblings() \
                and oCardSet.parent and oCardSet.inuse and \
                oCardSet.parent.id == self.__oPhysCardSet.parent.id:
            # inuse sibling card set going away while this affects display,
            # so reload
            self._oFrame.queue_reload()
        # Other card set deletions don't need to be watched here, since the
        # fiddling on parents should generate changed signals for us.

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
            # TODO: update cardset id -> profile map here
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
            delete_physical_card_set(self.view.sSetName)
            # Tell window to clean up
            # Card Set was deleted, so close up
            self._oFrame.close_frame()
            # Close any other open copies as well
            for oFrame in self._oMainWindow.find_cs_pane_by_set_name(
                    self.view.sSetName):
                oFrame.close_frame()


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
        if aSources[0] in ["Phys", PhysicalCardSet.sqlmeta.table]:
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
