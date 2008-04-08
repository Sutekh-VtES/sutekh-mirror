# EditPhysicalCardMappingDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Physical Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""
Dialog for handling the allocation of Physical Cards
across the different Physical Card Sets
"""

import gtk
from sutekh.gui.DBSignals import send_reload_signal
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.core.SutekhObjects import PhysicalCard, IAbstractCard, \
        IExpansion, MapPhysicalCardToPhysicalCardSet
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

def _gen_key(oPhysCard):
    """Generate a sort key

       We Generate a sort key - card name, expansion, card id
       This is to ensure stable ordering in the dialog
       """
    sName = oPhysCard.abstractCard.canonicalName
    if oPhysCard.expansion is None:
        sExpansion = ' Unspecified Expansion'
    else:
        sExpansion = oPhysCard.expansion.name
    sId = str(oPhysCard.id)
    return sName + ':' + sExpansion + ':' + sId

class EditPhysicalCardMappingDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # gtk class, so many pulic methods
    """
    Allow the user to change how the Physical Cards are allocated
    across the PhysicalCardSets. This does not allow the user to
    change the numbers assigned.
    """
    def __init__(self, oParent, dSelectedCards):
        """
        Create the dialog.
        For each abstract card, set up a table of cards and card sets
        with toggle buttons to control the mapping between the cards.
        The user can change the distribution within each abstract card
        freely, but can't change the number allocated to each card set
        """
        super(EditPhysicalCardMappingDialog, self).__init__(
                'Physical Card Set card allocation', oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        # This is horrible, and should be done by leveraging the
        # flitering work to get proper joins
        self.dPhysCards = {}
        self.dCardSets = {}
        # pylint: disable-msg=E1101
        # vbox & IExpansion confuses pylint
        self._get_card_sets(dSelectedCards)
        if len(self.dCardSets.keys()) == 0:
            # Not assigned to any card sets, so we become a complaint
            oIcon = gtk.Image()
            oIcon.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
            oHBox = gtk.HBox()
            oError = gtk.Label("Cards selected Not assigned to any card sets")
            oHBox.pack_start(oIcon)
            oHBox.pack_start(oError)
            self.vbox.pack_start(oHBox)
            self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            self.connect("response", lambda dlg, resp: dlg.destroy())
        else:
            self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            self.connect("response", self.button_response)
            # self.dCardSets has all the CardSets of interest, and the counts
            # for each card
            # self.dPhysCards has a mapping of card set membership
            # We create a table of items and such to handle everything
            self.oTable = self._create_table()
            self.vbox.pack_start(AutoScrolledWindow(self.oTable, True))
            self.set_default_size(600, 600)
            self.aNumbersNotMatched = []
        self.show_all()

    def _get_card_sets(self, dSelectedCards):
        """Extract the list of relevant card sets from the list of
           selected cards."""
        # pylint: disable-msg=E1101
        # IExpansion & IAbstractCard confuses pylint
        for sAbsCardName, dExpansions in dSelectedCards.iteritems():
            oAbstractCard = IAbstractCard(sAbsCardName)
            self.dPhysCards.setdefault(oAbstractCard, {})
            for sExpansion in dExpansions:
                if sExpansion != 'None':
                    if sExpansion == '  Unspecified Expansion':
                        iThisExpID = None
                    else:
                        iThisExpID = IExpansion(sExpansion).id
                    aPhysCards = PhysicalCard.selectBy(
                            abstractCardID=oAbstractCard.id,
                            expansionID=iThisExpID)
                else:
                    aPhysCards = PhysicalCard.selectBy(
                            abstractCardID=oAbstractCard.id)
                for oPhysCard in aPhysCards:
                    self.dPhysCards[oAbstractCard].setdefault(oPhysCard, [])
                    for oMap in MapPhysicalCardToPhysicalCardSet.selectBy(
                            physicalCardID=oPhysCard.id):
                        oCS = oMap.physicalCardSet
                        self.dPhysCards[oAbstractCard][oPhysCard].append(oCS)
                        self.dCardSets.setdefault(oCS, {})
                        self.dCardSets[oCS].setdefault(oAbstractCard, 0)
                        self.dCardSets[oCS][oAbstractCard] += 1

    def _create_table(self):
        """Create and pouplate the gtk.Table for this dialog"""
        oTable = gtk.Table()
        iTableWidth = len(self.dCardSets.keys())
        oTable.attach(gtk.Label('Cards'), 0, 1, 0, 1)
        iRow = 1
        # Setup the row labels for the table
        for oAbstractCard, dPhysMap in self.dPhysCards.iteritems():
            oTable.resize(iRow, iTableWidth)
            for oPhysCard in sorted(dPhysMap, key=_gen_key):
                if oPhysCard.expansion is not None:
                    sLabel = oAbstractCard.name + ':' + \
                            oPhysCard.expansion.name
                else:
                    sLabel = oAbstractCard.name + ': Unspecified expansion'
                oTable.attach(gtk.Label(sLabel), 0, 1, iRow, iRow + 1)
                iRow += 1
                oTable.resize(iRow, iTableWidth)
            oTable.attach(gtk.Label("Totals for %s : " % oAbstractCard.name) ,
                    0, 1, iRow, iRow + 1)
            iRow += 1
        iCol = 1
        for oCardSet in sorted(self.dCardSets):
            # Set the column header
            oTable.attach(gtk.Label(oCardSet.name), iCol, iCol + 1, 0, 1,
                    xpadding=2)
            iRow = 1
            # Fill the table with checkboxes, and connect the toggled
            # method
            for oAbstractCard, dPhysMap in self.dPhysCards.iteritems():
                if self.dCardSets[oCardSet].has_key(oAbstractCard):
                    oTotalLabel = gtk.Label(str(self.dCardSets[oCardSet][
                        oAbstractCard]))
                    dColumnDetails = { 'cardset' : oCardSet,
                            'label' : oTotalLabel,
                            'card' : oAbstractCard }
                    # These details are shared by multiple checkboxes
                    for oPhysCard in sorted(dPhysMap, key=_gen_key):
                        aCardSets = dPhysMap[oPhysCard]
                        oCheckBox = gtk.CheckButton()
                        oCheckBox.set_active(oCardSet in aCardSets)
                        oAlignBox = gtk.Alignment(xalign=0.5)
                        oAlignBox.add(oCheckBox)
                        oTable.attach(oAlignBox, iCol, iCol + 1, iRow,
                                iRow + 1)
                        iRow += 1
                        oCheckBox.connect('toggled', self.do_toggle,
                                dColumnDetails, aCardSets)
                else:
                    # None of these cards are members of the card set,
                    # so leave this section of the column blank
                    oTotalLabel = gtk.Label('0')
                    iRow += len(dPhysMap)
                oTable.attach(oTotalLabel, iCol, iCol + 1, iRow, iRow + 1)
                iRow += 1
            iCol += 1
        return oTable

    def do_toggle(self, oWidget, dColumnDetails, aCardSetMapping):
        """
        Handle toggle button actions
        Update the associated lists, and the displayed totals
        """
        oTotLabel = dColumnDetails['label']
        sLabel = oTotLabel.get_label()
        iTot = int(sLabel.split(':')[0])
        if oWidget.get_active():
            iTot += 1
            aCardSetMapping.append(dColumnDetails['cardset'])
        else:
            iTot -= 1
            aCardSetMapping.remove(dColumnDetails['cardset'])
        iCorrectTotal = self.dCardSets[dColumnDetails['cardset']][
                dColumnDetails['card']]
        if iTot != iCorrectTotal:
            if iTot < iCorrectTotal:
                sSign = '-'
            else:
                sSign = ''
            oTotLabel.set_markup('%d:<b>%s%d</b>' % (iTot, sSign,
                abs(iCorrectTotal - iTot)))
            if oTotLabel not in self.aNumbersNotMatched:
                self.aNumbersNotMatched.append(oTotLabel)
        else:
            oTotLabel.set_label(str(iTot))
            if oTotLabel in self.aNumbersNotMatched:
                self.aNumbersNotMatched.remove(oTotLabel)
        oTotLabel.show()

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """
        Update the card sets in response to the user pressing OK
        """
        if iResponse == gtk.RESPONSE_OK:
            if len(self.aNumbersNotMatched) > 0:
                do_complaint_error("New allocation doesn't match on the"
                        " numbers")
                return
            else:
                # OK, numbers match, so now re-assign the cards
                for oAbstractCard, dPhysMap in self.dPhysCards.iteritems():
                    bSignal = False
                    # Not touching the GUI, so sorted not needed
                    for oPhysCard, aNewCardSets in dPhysMap.iteritems():
                        aOldCardSets = [x.physicalCardSet for x in
                                MapPhysicalCardToPhysicalCardSet.selectBy(
                                    physicalCardID=oPhysCard.id)]
                        for oCardSet in aOldCardSets:
                            if oCardSet not in aNewCardSets:
                                oCardSet.removePhysicalCard(oPhysCard.id)
                                bSignal = True
                        for oCardSet in aNewCardSets:
                            if oCardSet not in aOldCardSets:
                                oCardSet.addPhysicalCard(oPhysCard.id)
                                bSignal = True
                    if bSignal:
                        send_reload_signal(oAbstractCard)
        self.destroy()
