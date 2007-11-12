# Dialog for handling Physical Card Set allocation across
# Physical Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk
from sutekh.gui.DBSignals import send_reload_signal
from sutekh.core.SutekhObjects import PhysicalCard, IAbstractCard, \
        IExpansion, MapPhysicalCardToPhysicalCardSet

class EditPhysicalCardMappingDialog(gtk.Dialog):
    """
    Allow the user to change how the Physical Cards are allocated
    across the PhysicalCardSets. This does not allow the user to
    change the numbers assigned.
    """
    def __init__(self, oParent, dSelectedCards):
        super(EditPhysicalCardMappingDialog, self).__init__(
                'Physical Card Set card allocation', oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        # This is horrible, and should be done by leveraging the
        # flitering work to get proper joins
        self.dPhysCards = {}
        self.dCardSets = {}
        for sAbsCardName, dExpansions in dSelectedCards.iteritems():
            oAbstractCard = IAbstractCard(sAbsCardName)
            self.dPhysCards.setdefault(oAbstractCard, {})
            for sExpansion, iCnt in dExpansions.iteritems():
                if sExpansion != 'None':
                    if sExpansion == '  Unspecified Expansion':
                        iThisExpID = None
                    else:
                        iThisExpID = IExpansion(sExpansion).id
                    aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbstractCard.id,
                        expansionID=iThisExpID)
                else:
                    aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbstractCard.id)
                for oPhysCard in aPhysCards:
                    self.dPhysCards[oAbstractCard].setdefault(oPhysCard,[])
                    for oMap in MapPhysicalCardToPhysicalCardSet.selectBy(physicalCardID=oPhysCard.id):
                        oCS = oMap.physicalCardSet
                        self.dPhysCards[oAbstractCard][oPhysCard].append(oCS)
                        self.dCardSets.setdefault(oCS, {})
                        self.dCardSets[oCS].setdefault(oAbstractCard, 0)
                        self.dCardSets[oCS][oAbstractCard] += 1
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
            iTableWidth = len(self.dCardSets.keys())
            self.oTable = gtk.Table()
            oLabel = gtk.Label('Cards')
            self.oTable.attach(oLabel, 0, 1, 0, 1)
            k = 1
            for oAbstractCard, dPhysMap in self.dPhysCards.iteritems():
                self.oTable.resize(k, iTableWidth)
                for oPhysCard in dPhysMap.keys():
                    if oPhysCard.expansion is not None:
                        sLabel = oAbstractCard.name + ':' + oPhysCard.expansion.name
                    else:
                        sLabel = oAbstractCard.name + ': Unspecified expansion'
                    oLabel = gtk.Label(sLabel)
                    self.oTable.attach(oLabel, 0, 1, k, k+1)
                    k += 1
                    self.oTable.resize(k, iTableWidth)
                oLabel = gtk.Label("Totals for %s : " % oAbstractCard.name)
                self.oTable.attach(oLabel, 0, 1, k, k+1)
                k += 1
            j = 1
            for oCardSet in self.dCardSets.keys():
                oLabel = gtk.Label(oCardSet.name)
                self.oTable.attach(oLabel, j, j+1, 0, 1, xpadding=2)
                k = 1
                for oAbstractCard, dPhysMap in self.dPhysCards.iteritems():
                    if self.dCardSets[oCardSet].has_key(oAbstractCard):
                        oTotalLabel = gtk.Label(str(self.dCardSets[oCardSet][oAbstractCard]))
                        for oPhysCard, aCardSets in dPhysMap.iteritems():
                            oCheckBox = gtk.CheckButton()
                            oCheckBox.set_active(oCardSet in aCardSets)
                            oAlignBox = gtk.Alignment(xalign=0.5)
                            oAlignBox.add(oCheckBox)
                            self.oTable.attach(oAlignBox, j, j+1, k, k+1)
                            k += 1
                            oCheckBox.connect('toggled', self.do_toggle, oTotalLabel, 
                                    oCardSet, oAbstractCard, aCardSets)
                    else:
                        oTotalLabel = gtk.Label('0')
                        for oPhysCard, aCardSets in dPhysMap.iteritems():
                            k += 1
                    self.oTable.attach(oTotalLabel, j, j+1, k, k+1)
                    k += 1
                j += 1
            self.vbox.pack_start(self.oTable)
            self.aNumbersNotMatched = []
        self.show_all()

    def do_toggle(self, oWidget, oTotLabel, oCardSet, oAbsCard, aCardSetMapping):
        sLabel = oTotLabel.get_label()
        iTot = int(sLabel.split(':')[0])
        if oWidget.get_active():
            iTot += 1
            aCardSetMapping.append(oCardSet)
        else:
            iTot -= 1
            aCardSetMapping.remove(oCardSet)
        iCorrectTotal = self.dCardSets[oCardSet][oAbsCard]
        if iTot > iCorrectTotal:
            oTotLabel.set_markup(str(iTot)+':<b> +'+str(iTot - iCorrectTotal)+'</b>')
            if oTotLabel not in self.aNumbersNotMatched:
                self.aNumbersNotMatched.append(oTotLabel)
        elif iTot < iCorrectTotal:
            oTotLabel.set_markup(str(iTot)+':<b> -'+str(iCorrectTotal - iTot)+'</b>')
            if oTotLabel not in self.aNumbersNotMatched:
                self.aNumbersNotMatched.append(oTotLabel)
        else:
            oTotLabel.set_label(str(iTot))
            if oTotLabel in self.aNumbersNotMatched:
                self.aNumbersNotMatched.remove(oTotLabel)
        oTotLabel.show()

    def button_response(self, oWidget, iResponse):
        if iResponse == gtk.RESPONSE_OK:
            if len(self.aNumbersNotMatched) > 0:
                oComplaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE, "New allocation doesn't match on the numbers")
                oComplaint.connect("response", lambda dlg, resp: dlg.destroy())
                oComplaint.run()
                return
            else:
                # OK, numbers match, so now re-assign the cards 
                for oAbstractCard, dPhysMap in self.dPhysCards.iteritems():
                    bSignal = False
                    for oPhysCard, aNewCardSets in dPhysMap.iteritems():
                        aOldCardSets = [x.physicalCardSet for x in 
                                MapPhysicalCardToPhysicalCardSet.selectBy(physicalCardID=oPhysCard.id)]
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
