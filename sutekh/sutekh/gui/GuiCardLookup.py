# CardLookup.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names, presenting the user with a GUI
   to pick unknown cards from.
   """

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCard
from sutekh.core.CardLookup import AbstractCardLookup, PhysicalCardLookup, \
        LookupFailed
from sutekh.core.Filters import CardNameFilter
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.gui.AbstractCardView import AbstractCardView
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class dummyController(object):
    """Dummy controller class, so we can use the card views directly"""
    def __init__(self, sFilterType):
        self.sFilterType = sFilterType

    filtertype = property(fget=lambda self: self.sFilterType)

    def set_card_text(self, sCardName):
        pass

class ACLlookupView(AbstractCardView):
    """
    Specialised version for the Card Lookup
    """
    def __init__(self, oDialogWindow, oConfig):
        oController = dummyController('AbstractCard')
        super(ACLlookupView, self).__init__(oController, oDialogWindow, oConfig)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def get_selected_card(self):
        sNewName = 'No Card'
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName = self._oModel.getCardNameFromPath(oPath)
        return sNewName

class PCLwithNumbersView(PhysicalCardView):
    """
    Also show current allocation of cards in the physical card view
    """
    def __init__(self, oDialogWindow, oConfig):
        oController = dummyController('PhysicalCard')
        super(PCLwithNumbersView, self).__init__(oController, oDialogWindow, oConfig)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def get_selected_card(self):
        sNewName = 'No Card'
        sExpansion = '  Unpecified Expansion'
        oModel, aSelection = self.get_selection().get_selected_rows()
        for oPath in aSelection:
            sNewName, sExpansion, iCount, iDepth = self._oModel.get_all_from_path(oPath)
        if sExpansion is None:
            sExpansion = ''
        return sNewName, sExpansion

    def set_card_set_holder_numbers(self, aPhysCards):
        """Mark numbers already found for the card set in the model"""
        pass

class GuiLookup(AbstractCardLookup, PhysicalCardLookup):
    """Lookup AbstractCards. Use the user as the AI if a simple lookup fails.
       """

    def __init__(self, oConfig):
        self._oConfig = oConfig

    def lookup(self, aNames, sInfo):
        dCards = {}
        dUnknownCards = {}

        for sName in aNames:
            try:
                oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
                dCards[sName] = oAbs
            except SQLObjectNotFound:
                dUnknownCards[sName] = None

        if dUnknownCards:
            bContinue = self._do_handle_unknown_abstract_cards(dUnknownCards, sInfo)
        else:
            bContinue = True

        if not bContinue:
            raise LookupFailed("Lookup of missing cards aborted by the user.")

        for sName, sNewName in dUnknownCards.items():
            if sNewName is None:
                continue
            try:
                oAbs = AbstractCard.byCanonicalName(sNewName.encode('utf8').lower())
                dUnknownCards[sName] = oAbs
            except SQLObjectNotFound:
                raise RuntimeError("Unexpectedly encountered missing abstract card '%s'." % sName)

        return [(sName in dCards and dCards[sName] or dUnknownCards[sName]) for sName in aNames]

    def physical_lookup(self, dCardExpansions, dNameCards, sInfo):
        aCards = []
        dUnknownCards = {}
        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is not None:
                try:
                    for oExpansion in dCardExpansions[sName]:
                        iCnt = dCardExpansions[sName][oExpansion]
                        if oExpansion is not None:
                            aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id,
                                    expansionID=oExpansion.id)
                        else:
                            aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id,
                                    expansionID=None)
                        for oPhys in aPhysCards:
                            if oPhys not in aCards \
                                    and iCnt > 0:
                                aCards.append(oPhys)
                                iCnt -= 1
                                if iCnt == 0:
                                    break
                        if iCnt > 0:
                            dUnknownCards.setdefault((oAbs.name, oExpansion), 0)
                            dUnknownCards[(oAbs.name, oExpansion)] = iCnt
                except SQLObjectNotFound:
                    for oExpansion in dCardExpansions[sName]:
                        iCnt = dCardExpansions[sName][oExpansion]
                        if iCnt > 0:
                            dUnknownCards.setdefault((oAbs.name, oExpansion), 0)
                            dUnknownCards[(oAbs.name, oExpansion)] = iCnt
        if dUnknownCards:
            # We need to lookup cards in the physical card view
            if not self._do_handle_unknown_physical_cards(dUnknownCards, aCards, sInfo):
                raise LookupFailed("Lookup of missing cards aborted by the user.")

        return aCards

    def _do_handle_unknown_physical_cards(self, dUnknownCards, aPhysCards, sInfo):
        """Handle unknwon physical cards

           We allow the user to select the correct replacements from the
           Physical Card List
        """

        oUnknownDialog = gtk.Dialog("Unknown Physical cards found importing %s" % sInfo, None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oPhysCardView = PCLwithNumbersView(oUnknownDialog, self._oConfig)

        oMesgLabel1 = gtk.Label()
        oMesgLabel2 = gtk.Label()

        sMsg1 = "While importing " + sInfo + "\n"
        sMsg1 += "The following cards could not be found in the Physical Card List:"
        sMsg1 += "\nChoose how to handle these cards?\n"
        sMsg2 = "OK creates the card set, "
        sMsg2 += "Cancel aborts the creation of the card set"

        oMesgLabel1.set_text(sMsg1)
        oUnknownDialog.vbox.pack_start(oMesgLabel1)

        dReplacement = {}
        for sName, oExpansion in dUnknownCards:
            iCnt = dUnknownCards[(sName, oExpansion)]
            if iCnt <= 0:
                # Should never happen, but ensure robustness against parser
                # errors
                continue
            oBox = gtk.HBox()
            if oExpansion is not None:
                oLabel = gtk.Label("%d copies of %s from expansion %s Not found: Replace with " % (iCnt, sName, oExpansion.name) )
            else:
                oLabel = gtk.Label("%d copies of %s with no expansion specified Not found: Replace with " % (iCnt, sName) )
            oBox.pack_start(oLabel)
            dReplacement[(sName, oExpansion)] = gtk.Label("No Card")
            oBox.pack_start(dReplacement[(sName, oExpansion)])
            oUnknownDialog.vbox.pack_start(oBox)

            oBox = gtk.HButtonBox()
            oButton1 = gtk.Button("Use selected Physical Card")
            oButton2 = gtk.Button("Ignore this Card")
            oButton3 = gtk.Button("Filter Physical Cards with best guess")
            oButton1.connect("clicked", self._set_to_selection,
                    dReplacement[(sName, oExpansion)], 'Physical', iCnt, aPhysCards)
            oButton2.connect("clicked", self._set_ignore,
                    dReplacement[(sName, oExpansion)])
            oButton3.connect("clicked", self._set_filter, sName, 'Physical')
            oBox.pack_start(oButton1)
            oBox.pack_start(oButton2)
            oBox.pack_start(oButton3)
            oUnknownDialog.vbox.pack_start(oBox)

        oMesgLabel2.set_text(sMsg2)

        oUnknownDialog.vbox.pack_start(oMesgLabel2)
        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()

        oUnknownDialog.destroy()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the list of Physical Cards 
            for sName, oExpansion in dUnknownCards:
                aNames = dReplacement[sName].get_text().split('  exp: ')
                sNewNames = aNames[0]
                if len(aNames) > 1:
                    sExpName = aNames[1]
                    try:
                        iExpID = IExpansion(sExpName).id
                    except SQLObjectNotFound:
                        iExpID = None
                else:
                    sExpName = ''
                iCnt = dUnknownCards[(sName, oExpansion)]
                if sNewName != "No Card":
                    # Find First physical card that matches this name
                    # that's not in aPhysCards
                    # FIXME: will break with proper expansion support
                    oAbs = AbstractCard.byCanonicalName(sNewName.encode('utf8').lower())
                    if sExpName != '':
                        aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id, expansionID=iExpID)
                    else:
                        aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id)
                    for oCard in aCandPhysCards:
                        if oCard not in aPhysCards:
                            if iCnt > 0:
                                iCnt -= 1
                                aPhysCards.append(oCard)
            return True
        else:
            return False

    def _do_handle_unknown_abstract_cards(self, dUnknownCards, sInfo):
        """Handle the list of unknown abstract cards.

           We allow the user to select the correct replacements from the Abstract
           Card List
           """
        oUnknownDialog = gtk.Dialog("Unknown cards found importing %s" % sInfo, None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oAbsCardView = ACLlookupView(oUnknownDialog, self._oConfig)
        oMesgLabel1 = gtk.Label()
        oMesgLabel2 = gtk.Label()

        sMsg1 = "While importing %s\n" \
                "The following card names could not be found:\n" \
                "Choose how to handle these cards?\n" % (sInfo)
        sMsg2 = "OK creates the card set, " \
                "Cancel aborts the creation of the card set"

        oMesgLabel1.set_text(sMsg1)
        oUnknownDialog.vbox.pack_start(oMesgLabel1, False, False)

        oButtonBox = gtk.VBox()
        oHBox = gtk.HBox()
        oViewWin = AutoScrolledWindow(oAbsCardView)
        oViewWin.set_size_request(200, 600)
        oHBox.pack_start(oViewWin, True, True)

        oFilterDialogButton = gtk.Button("Specify Filter")
        oFilterApplyButton = gtk.CheckButton("Apply Filter to view")
        oFilterButtons = gtk.HBox()

        oFilterButtons.pack_start(oFilterDialogButton)
        oFilterButtons.pack_start(oFilterApplyButton)
        oFilterDialogButton.connect('clicked', self._run_filter_dialog, oAbsCardView, oFilterApplyButton)
        oFilterApplyButton.connect("toggled", self._toggle_apply_filter, oAbsCardView)

        # Fill in the Cards and options
        dReplacement = {}
        for sName in dUnknownCards:
            oBox = gtk.HBox()
            oLabel = gtk.Label("%s is Unknown: Replace with " % sName)
            oBox.pack_start(oLabel)
            dReplacement[sName] = gtk.Label("No Card")
            oBox.pack_start(dReplacement[sName])
            oButtonBox.pack_start(oBox)

            oBox = gtk.HButtonBox()
            oButton1 = gtk.Button("Use selected Abstract Card")
            oButton2 = gtk.Button("Ignore this Card")
            oButton3 = gtk.Button("Filter Abstract Cards with best guess")
            # Count and physical card list don't matter here, so stub values
            oButton1.connect("clicked", self._set_to_selection,
                    dReplacement[sName], 'Abstract', 1, oAbsCardView, [])
            oButton2.connect("clicked", self._set_ignore,
                    dReplacement[sName])
            oButton3.connect("clicked", self._set_filter, oAbsCardView, sName, oFilterApplyButton)
            oBox.pack_start(oButton1)
            oBox.pack_start(oButton2)
            oBox.pack_start(oButton3)
            oButtonBox.pack_start(oBox)

        oButtonBox.pack_start(gtk.HSeparator())
        oButtonBox.pack_start(oFilterButtons)

        oHBox.pack_start(oButtonBox, False, False)
        
        oUnknownDialog.vbox.pack_start(oHBox, True, True)

        oMesgLabel2.set_text(sMsg2)

        oUnknownDialog.vbox.pack_start(oMesgLabel2)
        oUnknownDialog.vbox.show_all()

        iResponse = oUnknownDialog.run()

        oUnknownDialog.destroy()

        if iResponse == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the Holder
            for sName in dUnknownCards:
                aNames = dReplacement[sName].get_text().split('  exp: ')
                sNewName = aNames[0]
                if sNewName != "No Card":
                    dUnknownCards[sName] = sNewName
            return True
        else:
            return False

    def _set_to_selection(self, oButton, oRepLabel, sType, iCnt, oView, aPhysCards):
        """Set the replacement to the selected entry"""
        # We hanlde PhysicalCards on a like-for-like matching case.
        # For cases where the user selects an expansion with too few
        # cards, but where there are enough phyiscal cards, we do the best we can
        sExpansion = ''
        sNewName = oView.get_selected_card()
        
        if sType == 'Physical' and \
                not self._check_physical_cards(sNewName, iCnt, aPhysCards):
            oComplaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                gtk.BUTTONS_OK, "Not enough copies of %s" % sNewName)
            oComplaint.connect("response", lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return
        elif sType == 'Physical' and \
                not self._check_physical_cards_with_expansion(sNewName,
                        sExpansion, iCnt, aPhysCards):
            oComplaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                gtk.BUTTONS_OK,
                "Not enough copies of %s from expansion %s\n." \
                "Ignoring the expansion specification" % (sNewName, sExpansion))
            oComplaint.connect("response", lambda oW, oResp: oW.destroy())
            oComplaint.run()
            sExpansion = ''
        oRepLabel.hide()
        if sExpansion != '':
            oRepLabel.set_text(sNewName + "  exp: " + sExpansion)
        else:
            oRepLabel.set_text(sNewName)
        oRepLabel.show()

    def _check_physical_cards(self, sName, iCnt, aPhysCards):
        """Check that there are enough physical cards to fulfill the
           request
        """
        oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
        aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id)
        for oCard in aCandPhysCards:
            if oCard not in aPhysCards:
                # Card is a feasible replacement
                iCnt -= 1
                if iCnt == 0:
                    return True # Can fulfill the request
        return False

    def _check_physical_cards_with_expansion(self, sName, sExpansion, iCnt, aPhysCards):
        """Check that there are enough physical cards of the specified expansion
           to fulfill the request
        """
        oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
        try:
            iExpID = IExpansion(sExpansion).id
        except SQLObjectNotFound:
            iExpID = None
        aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id, expansionID=iExpID)
        for oCard in aCandPhysCards:
            if oCard not in aPhysCards:
                # Card is a feasible replacement
                iCnt -= 1
                if iCnt == 0:
                    return True # Can fulfill the request
        return False

    def _run_filter_dialog(self, oButton, oView, oToggleButton):
        oView.getFilter(None)
        if oToggleButton.get_active() != oView._oModel.applyfilter:
            oToggleButton.set_active(oView._oModel.applyfilter)

    def _run_filter(self, oView, oFilter, oToggleButton):
        oView.getModel().selectfilter = oFilter
        if not oToggleButton.get_active():
            oToggleButton.set_active(True)
        else:
            oView.load()

    def _toggle_apply_filter(self, oButton, oView):
        oView.getModel().applyfilter = oButton.get_active()
        oView.load()

    def _set_filter(self, oButton, oView, sName, oToggleButton):
        oFilter = self._best_guess_filter(sName)
        self._run_filter(oView, oFilter, oToggleButton)

    def _best_guess_filter(self, sName):
        # Set the filter on the Card List to one the does a
        # Best guess search
        sFilterString = ' ' + sName.lower() + ' '
        # Kill the's in the string
        sFilterString = sFilterString.replace(' the ', '')
        # Kill commas, as possible issues
        sFilterString = sFilterString.replace(',', '')
        # Wildcard spaces
        sFilterString = sFilterString.replace(' ', '%').lower()
        # Stolen semi-concept from soundex - replace vowels with wildcards
        # Should these be %'s ??
        # (Should at least handle the Rotscheck variation as it stands)
        sFilterString = sFilterString.replace('a', '_')
        sFilterString = sFilterString.replace('e', '_')
        sFilterString = sFilterString.replace('i', '_')
        sFilterString = sFilterString.replace('o', '_')
        sFilterString = sFilterString.replace('u', '_')
        return CardNameFilter(sFilterString)

    def _set_ignore(self, oButton, oRepLabel):
        oRepLabel.hide()
        oRepLabel.set_text("No Card")
        oRepLabel.show()
