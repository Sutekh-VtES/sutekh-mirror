# CardSetController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Controller for the card sets"""

from sqlobject import SQLObjectNotFound
from sutekh.gui.CardSetManagementController import reparent_card_set, \
        check_ok_to_delete
from sutekh.gui.CardSetView import CardSetView
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.DBSignals import listen_reload, listen_row_destroy, \
        listen_row_update, send_reload_signal
from sutekh.core.SutekhObjects import IPhysicalCardSet, PhysicalCardSet, \
        AbstractCard, PhysicalCard, MapPhysicalCardToPhysicalCardSet, \
        IExpansion, Expansion
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog
from sutekh.SutekhUtility import delete_physical_card_set

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
        # We need to cache this for physical_card_deleted checks
        self.__aPhysCardIds = []
        self.__aAbsCardIds = []
        for oPC in self.__oPhysCardSet.cards:
            oAC = oPC.abstractCard
            self.__aAbsCardIds.append(oAC.id)
            self.__aPhysCardIds.append(oPC.id)
        # Listen on card signals
        listen_row_destroy(self.card_deleted, MapPhysicalCardToPhysicalCardSet)
        listen_reload(self.cards_changed, PhysicalCardSet)
        # listen on card set signals
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
            # inuse sibling card set going away whel this affects display,
            # so reload
            self._oFrame.queue_reload()
        # Other card set deletions don't need to be watched here, since the
        # fiddling on parents should generate changed signals for us.

    def card_deleted(self, oPhysCard, fPostFuncs=None):
        """Listen on card removals from the mapping table.

           Needed so we can updated the model if a card in this set
           is deleted.
           """
        print 'Mapping Table row delete'
        print oPhysCard
        return
        # We get here after we have removed the card from the card set,
        # but before it is finally deleted from the table, so it's no
        # longer in self.__oPhysCards.
        #if oPhysCard.id in self.__aPhysCardIds:
        #    self.__aPhysCardIds.remove(oPhysCard.id)
        #    oAC = oPhysCard.abstractCard
        #    self.__aAbsCardIds.remove(oAC.id)
        #    # Update model
        #    if oPhysCard.expansion is not None:
        #        self.model.dec_card_expansion_by_name(oAC.name,
        #                oPhysCard.expansion.name)
        #    else:
        #        self.model.dec_card_expansion_by_name(oAC.name,
        #                oPhysCard.expansion)
        #    self.model.dec_card_by_name(oAC.name)

    def cards_changed(self, oCardSet, oPhysCard):
        """Listen for card changed signals.

           Need to listen to special signal, since SQLObject only sends
           signals when an instance is created, which is not the case
           when using oSet.addPhysicalCard
           Does rely on all creators calling send_reload_signal.
           """
        print 'Mapping Table card set reload signal'
        print oCardSet, oPhysCard
        return
        #if oPhysCard.id in self.__aPhysCardIds and 'expansionID' in dChanges:
        #    # Changing a card assigned to the card list
        #    iNewID = dChanges['expansionID']
        #    oAC = oPhysCard.abstractCard
        #    if oPhysCard.expansion is not None:
        #        self.model.dec_card_expansion_by_name(oAC.name,
        #                oPhysCard.expansion.name)
        #    else:
        #        self.model.dec_card_expansion_by_name(oAC.name, None)
        #    if iNewID is not None:
        #        oNewExpansion = list(Expansion.selectBy(id=iNewID))[0]
        #        sExpName = oNewExpansion.name
        #    else:
        #        sExpName = None
        #    self.model.inc_card_expansion_by_name(oAC.name, sExpName)

    def set_card_text(self, sCardName):
        """Set card text to reflect selected card."""
        self._oMainWindow.set_card_text(sCardName)

    def inc_card(self, sName, sExpansion):
        """Returns True if a card was successfully added, False otherwise."""
        return self.add_card(sName, sExpansion)

    def dec_card(self, sName, sExpansion):
        """Returns True if a card was successfully removed, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        # find if there's a physical card of that name in the Set
        if not sExpansion:
            # Not expansion specified, so consider all physical cards
            aPhysCards = list(PhysicalCard.selectBy(
                abstractCardID=oAbsCard.id))
        else:
            if sExpansion == self.model.sUnknownExpansion:
                iExpID = None
            else:
                iExpID = IExpansion(sExpansion).id
            aPhysCards = list(PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                expansionID = iExpID))
        for oCard in aPhysCards:
            # Need to remove a single physical card from the mapping table
            # Can't use PhysicalCardSet.remove, as that remove all cards
            aCandCards = list(MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id,
                    physicalCardSetID=self.__oPhysCardSet.id))
            if len(aCandCards) > 0:
                # Found candidates, so remove last one
                MapPhysicalCardToPhysicalCardSet.delete(aCandCards[-1].id)
                # Update Model
                self.model.dec_card_by_name(oAbsCard.name)
                # Update internal card list
                self.__aPhysCardIds.remove(oCard.id)
                self.__aAbsCardIds.remove(oAbsCard.id)
                if oCard.expansion is not None:
                    self.model.dec_card_expansion_by_name(oAbsCard.name,
                            oCard.expansion.name)
                else:
                    self.model.dec_card_expansion_by_name(oAbsCard.name, None)
                return True
        return False

    def add_card(self, sName, sExpansion):
        """Returns True if a card was successfully added, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        if not sExpansion or sExpansion == self.model.sUnknownExpansion:
            iExpID = None
        else:
            iExpID = IExpansion(sExpansion).id
        aPhysCards = list(PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
            expansionID = iExpID))

        if len(aPhysCards) > 0:
            oCard = aPhysCards[0]
            self.__oPhysCardSet.addPhysicalCard(oCard.id)
            send_reload_signal(self.__oPhysCardSet, oCard)
            self.__oPhysCardSet.sync()
            self.__aPhysCardIds.append(oCard.id)
            self.__aAbsCardIds.append(oAbsCard.id)
            # Update Model
            self.model.inc_card_by_name(oAbsCard.name)
            if oCard.expansion is not None:
                self.model.inc_card_expansion_by_name(oAbsCard.name,
                        oCard.expansion.name)
            else:
                self.model.inc_card_expansion_by_name(oAbsCard.name, None)
            return True
        # Got here, so we failed to add
        return False

    def edit_annotations(self):
        """Show the annotations dialog and update the card set."""
        oEditAnn = EditAnnotationsDialog(self._oMainWindow,
                self.__oPhysCardSet)
        oEditAnn.run()
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        self.__oPhysCardSet.annotations = oEditAnn.get_data()
        self.__oPhysCardSet.syncUpdate()

    def edit_properties(self, oMenu):
        """Run the dialog to update the card set properties"""
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylint
        oProp = CreateCardSetDialog(self._oMainWindow,
                oCardSet=self.__oPhysCardSet)
        oProp.run()
        sName = oProp.get_name()
        if sName:
            # Passed, so update the card set
            self.__oPhysCardSet.name = sName
            self.view.sSetName = sName
            sAuthor = oProp.get_author()
            sComment = oProp.get_comment()
            oParent = oProp.get_parent()
            if sAuthor is not None:
                self.__oPhysCardSet.author = sAuthor
            if sComment is not None:
                self.__oPhysCardSet.comment = sComment
            if oParent != self.__oPhysCardSet.parent:
                reparent_card_set(self.__oPhysCardSet, oParent)
            self.__oPhysCardSet.syncUpdate()
            # Update frame menu
            self._oFrame.menu.update_card_set_menu(self.__oPhysCardSet)
            # Reload pcs_list, since we may have changed stuff
            self._oMainWindow.reload_pcs_list()

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
