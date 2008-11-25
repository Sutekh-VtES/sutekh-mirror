# CardSetController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Controller for the card sets"""

from sqlobject import SQLObjectNotFound
from sutekh.gui.CardSetManagementController import check_ok_to_delete, \
        update_card_set
from sutekh.gui.CardSetView import CardSetView
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.core.DBSignals import listen_row_destroy, listen_row_update, \
        send_changed_signal, disconnect_row_destroy, disconnect_row_update
from sutekh.core.SutekhObjects import IPhysicalCardSet, PhysicalCardSet, \
        AbstractCard, PhysicalCard, MapPhysicalCardToPhysicalCardSet, \
        IExpansion, IPhysicalCard
from sutekh.core.CardSetUtilities import delete_physical_card_set

class CardSetController(object):
    """Controller class for the Card Sets."""
    _sFilterType = 'PhysicalCard'

    def __init__(self, sName, oMainWindow, oFrame):
        # pylint: disable-msg=E1101
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
        # pylint: disable-msg=E1101
        # Pyprotocols confuses pylint
        if oCardSet.id == self.__oPhysCardSet.id and \
                dChanges.has_key('parentID'):
            # This card set's parent is changing
            # Update menu to reflect this
            self._oFrame.menu.check_parent_count_column(oCardSet.parent,
                    dChanges['parentID'])
            if self.model.changes_with_parent() or not dChanges['parentID']:
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

    # pylint: disable-msg=W0613
    # fPostFuncs is passed by SQLObject 0.10, but not by 0.9
    def card_set_deleted(self, oCardSet, fPostFuncs=None):
        """Listen for card set removal events.

           Needed if child card sets are deleted, for instance.
           """
        # pylint: disable-msg=E1101
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

    def toggle_icons(self, oWidget):
        """Toggle the icons display"""
        self.model.bUseIcons = oWidget.active
        self.view.reload_keep_expanded()

    def set_card_text(self, sCardName):
        """Set card text to reflect selected card."""
        self._oMainWindow.set_card_text(sCardName)

    def inc_card(self, sName, sExpansion, sCardSetName):
        """Returns True if a card was successfully added, False otherwise."""
        return self.add_card(sName, sExpansion, sCardSetName)

    def dec_card(self, sName, sExpansion, sCardSetName):
        """Returns True if a card was successfully removed, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            if sCardSetName:
                oThePCS = IPhysicalCardSet(sCardSetName)
            else:
                oThePCS = self.__oPhysCardSet
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())

            # find if there's a physical card of that name in the Set
            if not sExpansion:
                # Not expansion specified, so consider all physical cards
                aPhysCards = list(PhysicalCard.selectBy(
                    abstractCardID=oAbsCard.id))
            else:
                if sExpansion == self.model.sUnknownExpansion:
                    oExp = None
                else:
                    oExp = IExpansion(sExpansion)
                aPhysCards = [IPhysicalCard((oAbsCard, oExp))]
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

    def add_card(self, sName, sExpansion, sCardSetName):
        """Returns True if a card was successfully added, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            if sCardSetName:
                oThePCS = IPhysicalCardSet(sCardSetName)
            else:
                oThePCS = self.__oPhysCardSet
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())

            if not sExpansion or sExpansion == self.model.sUnknownExpansion:
                oExp = None
            else:
                oExp = IExpansion(sExpansion)
            oCard = IPhysicalCard((oAbsCard, oExp))
        except SQLObjectNotFound:
            # Any error means we bail
            return False

        oThePCS.addPhysicalCard(oCard.id)
        oThePCS.syncUpdate()
        # Signal to update the model
        send_changed_signal(oThePCS, oCard, 1)
        return True

    def edit_properties(self, oMenu):
        """Run the dialog to update the card set properties"""
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        oProp = CreateCardSetDialog(self._oMainWindow,
                oCardSet=self.__oPhysCardSet)
        oProp.run()
        sName = oProp.get_name()
        if sName:
            if sName != self.view.sSetName:
                self.view.update_name(sName)
            update_card_set(self.__oPhysCardSet, oProp, self._oMainWindow,
                    self._oFrame.menu)

    def update_to_new_db(self):
        """Update the internal card set to the new DB."""
        try:
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
                # pylint: disable-msg=W0612
                # iLoop is just loop counter
                # Use None to indicate this card set
                if aSources[0] == "Phys":
                    # Only ever add 1 when dragging from physiscal card list
                    self.add_card(sCardName, sExpansion, None)
                else:
                    for iLoop in range(iCount):
                        self.add_card(sCardName, sExpansion, None)
            return True
        else:
            return False

    def del_selected_cards(self, dSelectedData):
        """Helper function to delete the selected data."""
        for sCardName in dSelectedData:
            for sExpansion, iCount in dSelectedData[sCardName].iteritems():
                # pylint: disable-msg=W0612
                # iAttempt is loop counter
                for iAttempt in range(iCount):
                    # None as card set indicates this card set
                    if sExpansion != 'None':
                        self.dec_card(sCardName, sExpansion, None)
                    else:
                        self.dec_card(sCardName, None, None)

    def set_selected_card_count(self, dSelectedData, iNewCnt):
        """Helper function to set the selected cards to the specified number"""
        for sCardName in dSelectedData:
            for (sExpansion, sCardSetName), iCardCount in \
                    dSelectedData[sCardName].iteritems():
                # pylint: disable-msg=W0612
                # iAttempt is loop counter
                if iNewCnt < iCardCount:
                    # remove cards
                    for iAttempt in range(iCardCount - iNewCnt):
                        # None as card set indicates this card set
                        if sExpansion != 'None' and sExpansion != 'All':
                            self.dec_card(sCardName, sExpansion, sCardSetName)
                        else:
                            self.dec_card(sCardName, None, sCardSetName)
                elif iNewCnt > iCardCount:
                    # add cards
                    for iAttempt in range(iNewCnt - iCardCount):
                        # None as card set indicates this card set
                        if sExpansion != 'None' and sExpansion != 'All':
                            self.inc_card(sCardName, sExpansion, sCardSetName)
                        else:
                            self.inc_card(sCardName, None, sCardSetName)

    def alter_selected_card_count(self, dSelectedData, iChg):
        """Helper function to inc/dec the count for the selected cards"""
        for sCardName in dSelectedData:
            for (sExpansion, sCardSetName) in dSelectedData[sCardName]:
                # None as card set in inc_card/dec_Card indicates this card set
                if iChg == -1:
                    # remove cards
                    if sExpansion != 'None' and sExpansion != 'All':
                        self.dec_card(sCardName, sExpansion, sCardSetName)
                    else:
                        self.dec_card(sCardName, None, sCardSetName)
                elif iChg == 1:
                    # add cards
                    if sExpansion != 'None' and sExpansion != 'All':
                        self.inc_card(sCardName, sExpansion, sCardSetName)
                    else:
                        self.inc_card(sCardName, None, sCardSetName)
