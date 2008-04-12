# CardSetController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Controller for the card sets"""

from sqlobject import SQLObjectNotFound
from sutekh.gui.CardSetView import CardSetView
from sutekh.gui.DBSignals import listen_reload, listen_row_destroy, \
                                 listen_row_update
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet, \
        AbstractCard, PhysicalCard, MapPhysicalCardToPhysicalCardSet, \
        IExpansion, Expansion

class CardSetController(object):
    """Card Set Controller object.

       This is the base class for the Physical and Abstract Card Set
       Controllers.
       """
    def __init__(self, sName, cType, oMainWindow, oFrame):
        self._oMainWindow = oMainWindow
        self._oMenu = None
        self._oFrame = oFrame
        self._oView = CardSetView(oMainWindow, self, sName, cType)
        self._sFilterType = None

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    view = property(fget=lambda self: self._oView, doc="Associated View")
    model = property(fget=lambda self: self._oView._oModel, doc="View's Model")
    frame = property(fget=lambda self: self._oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def set_card_text(self, sCardName):
        """Set card text to reflect selected card."""
        self._oMainWindow.set_card_text(sCardName)

    def inc_card(self, sName, sExpansion):
        """Returns True if a card was successfully added, False otherwise."""
        return self.add_card(sName, sExpansion)

    def dec_card(self, sName, sExpansion):
        """Remove a card, implemented in derived classes"""
        pass

    def add_card(self, sName, sExpansion):
        """Add a card, implemented in derived classes"""
        pass

class PhysicalCardSetController(CardSetController):
    """Controller class for PhysicalCardSets."""
    def __init__(self, sName, oMainWindow, oFrame):
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        super(PhysicalCardSetController, self).__init__(
                sName, PhysicalCardSet, oMainWindow, oFrame)
        self.__oPhysCardSet = PhysicalCardSet.byName(sName)
        # We need to cache this for physical_card_deleted checks
        self.__aPhysCardIds = []
        self.__aAbsCardIds = []
        for oPC in self.__oPhysCardSet.cards:
            oAC = oPC.abstractCard
            self.__aAbsCardIds.append(oAC.id)
            self.__aPhysCardIds.append(oPC.id)
        self._sFilterType = 'PhysicalCard'
        listen_row_destroy(self.physical_card_deleted, PhysicalCard)
        listen_row_update(self.physical_card_changed, PhysicalCard)
        listen_reload(self.reload_card_set, PhysicalCard)

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

    def dec_card(self, sName, sExpansion):
        """Returns True if a card was successfully removed, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False

        # find if there's a physical card of that name in the Set
        if sExpansion is not None:
            # Specific Expansion specified by the user, so
            # just need to consider those cards
            if sExpansion == self.model.sUnknownExpansion:
                aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                        expansionID = None)
            else:
                iExpID = IExpansion(sExpansion).id
                aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                        expansionID = iExpID)
        else:
            # Need to consider all PhysicalCards
            aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id)
        for oCard in aPhysCards:
            if oCard.id in self.__aPhysCardIds:
                # Found one, so remove it
                self.__oPhysCardSet.removePhysicalCard(oCard.id)
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

        if sExpansion is not None:
            # Specific Expansion specified by the user, so
            # just need to consider those cards
            if sExpansion == self.model.sUnknownExpansion:
                aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                        expansionID = None)
            else:
                iExpID = IExpansion(sExpansion).id
                aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id,
                        expansionID = iExpID)
        else:
            # Need to consider all PhysicalCards
            aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbsCard.id)

        if aPhysCards.count() > 0:
            aCandCards = []
            for oCard in aPhysCards:
                # We want to add a card that's not in this expansion,
                if oCard.id not in self.__aPhysCardIds:
                    # We want the card in the fewest other card sets
                    # Should be effecient due to the Cached joins
                    aCandCards.append((oCard,
                        MapPhysicalCardToPhysicalCardSet.selectBy(
                            physicalCardID = oCard.id).count()))
            if len(aCandCards) < 1:
                # No card to be added
                return False
            aCandCards.sort(key=lambda x: x[1]) # sort by count
            oCard = aCandCards[0][0]
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

class AbstractCardSetController(CardSetController):
    """Controller class for AbstractCardSets."""
    def __init__(self, sName, oMainWindow, oFrame):
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        super(AbstractCardSetController, self).__init__(
                sName, AbstractCardSet, oMainWindow, oFrame)
        self.__oAbsCardSet = AbstractCardSet.byName(sName)
        self._sFilterType = 'AbstractCard'

    # pylint: disable-msg=W0613
    # sExpansion needed by function signature
    def dec_card(self, sName, sExpansion):
        """Returns True if a card was successfully removed, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False
        # find if there's a abstract card of that name in the Set
        oDBClass = self.model.cardclass
        aSubSet = list(oDBClass.selectBy(abstractCardID=oAbsCard.id,
            abstractCardSetID=self.__oAbsCardSet.id))
        if len(aSubSet) > 0:
            oDBClass.delete(aSubSet[-1].id)
            self.model.alter_card_count(oAbsCard.name, -1)
            return True
        return False

    # pylint: disable-msg=W0613
    # sExpansion needed by function signature
    def add_card(self, sName, sExpansion):
        """Returns True if a card was successfully added, False otherwise."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        try:
            oAbsCard = AbstractCard.byCanonicalName(sName.lower())
        except SQLObjectNotFound:
            return False
        # Add to the Set
        # This is much simpler than for PhysicalCardSets, as we don't have
        # to worry about whether the card exists in PhysicalCards or not
        self.__oAbsCardSet.addAbstractCard(oAbsCard.id)
        self.model.inc_card_by_name(oAbsCard.name)
        return True
