# CardSetController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Controller for the card sets"""

from sqlobject import SQLObjectNotFound
from sutekh.gui.CardSetManagementController import reparent_card_set
from sutekh.gui.CardSetView import CardSetView
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.DBSignals import listen_reload, listen_row_destroy, \
                                 listen_row_update
from sutekh.core.SutekhObjects import PhysicalCardSet, \
        AbstractCard, PhysicalCard, MapPhysicalCardToPhysicalCardSet, \
        IExpansion, Expansion
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog

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
        self.__oPhysCardSet = PhysicalCardSet.byName(sName)
        # We need to cache this for physical_card_deleted checks
        self.__aPhysCardIds = []
        self.__aAbsCardIds = []
        for oPC in self.__oPhysCardSet.cards:
            oAC = oPC.abstractCard
            self.__aAbsCardIds.append(oAC.id)
            self.__aPhysCardIds.append(oPC.id)
        listen_row_destroy(self.physical_card_deleted, PhysicalCard)
        listen_row_update(self.physical_card_changed, PhysicalCard)
        listen_reload(self.reload_card_set, PhysicalCard)
        # FIXME: Need signals to catch parent/child relationship changes,
        # so we do the right thing

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    view = property(fget=lambda self: self._oView, doc="Associated View")
    model = property(fget=lambda self: self._oView._oModel, doc="View's Model")
    frame = property(fget=lambda self: self._oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def reload_card_set(self, oAbsCard):
        """When changes happen that may effect this, reload.

           Cases are when card numbers in PCS change while this is editable,
           or the allocation of cards to physical card sets changes.
           """
        if oAbsCard.id in self.__aAbsCardIds:
            self.view.reload_keep_expanded()

    # pylint: disable-msg=W0613
    # fPostFuncs is passed by SQLObject 0.10, but not by 0.9
    def physical_card_deleted(self, oPhysCard, fPostFuncs=None):
        """Listen on physical card removals.

           Needed so we can updated the model if a card in this set
           is deleted.
           """
        # We get here after we have removed the card from the card set,
        # but before it is finally deleted from the table, so it's no
        # longer in self.__oPhysCards.
        if oPhysCard.id in self.__aPhysCardIds:
            self.__aPhysCardIds.remove(oPhysCard.id)
            oAC = oPhysCard.abstractCard
            self.__aAbsCardIds.remove(oAC.id)
            # Update model
            if oPhysCard.expansion is not None:
                self.model.dec_card_expansion_by_name(oAC.name,
                        oPhysCard.expansion.name)
            else:
                self.model.dec_card_expansion_by_name(oAC.name,
                        oPhysCard.expansion)
            self.model.dec_card_by_name(oAC.name)

    def physical_card_changed(self, oPhysCard, dChanges):
        """Listen on physical cards changed.

           Needed so we can update the model if a card in this set is
           changed.
           """
        if oPhysCard.id in self.__aPhysCardIds and 'expansionID' in dChanges:
            # Changing a card assigned to the card list
            iNewID = dChanges['expansionID']
            oAC = oPhysCard.abstractCard
            if oPhysCard.expansion is not None:
                self.model.dec_card_expansion_by_name(oAC.name,
                        oPhysCard.expansion.name)
            else:
                self.model.dec_card_expansion_by_name(oAC.name, None)
            if iNewID is not None:
                oNewExpansion = list(Expansion.selectBy(id=iNewID))[0]
                sExpName = oNewExpansion.name
            else:
                sExpName = None
            self.model.inc_card_expansion_by_name(oAC.name, sExpName)

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
        self.__oPhysCardSet.annotations = oEditAnn.get_data()
        self.__oPhysCardSet.syncUpdate()

    def edit_properties(self, oMenu):
        """Run the dialog to update the card set properties"""
        oOldParent = self.__oPhysCardSet.parent
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
            # We may well have changed stuff on the card list pane, so reload
            oMenu.update_card_set_menu(self.__oPhysCardSet, oOldParent)
