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

class GuiLookup(AbstractCardLookup, PhysicalCardLookup):
    """Lookup AbstractCards. Use the user as the AI if a simple lookup fails.
       """

    def __init__(self, oAbsCardView, oPhysCardView):
        # FIXME: Should this create an abstract card list view inside the
        #        dialog? For times when the abstract card list isn't visible?
        self._oAbsCardView = oAbsCardView
        self._oPhysCardView = oPhysCardView

    def lookup(self, aNames):
        dCards = {}
        dUnknownCards = {}

        for sName in aNames:
            try:
                oAbs = AbstractCard.byCanonicalName(sName.encode('utf8').lower())
                dCards[sName] = oAbs
            except SQLObjectNotFound:
                dUnknownCards[sName] = None

        if dUnknownCards:
            bContinue = self._doHandleUnknown(dUnknownCards)
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

    def physical_lookup(self, dCardExpansions, dNameCards):
        aCards = []
        dUnknownCards = {}
        for sName in dCardExpansions:
            oAbs = dNameCards[sName]
            if oAbs is not None:
                try:
                    aPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id)
                    for sExpansion in dCardExpansions[sName]:
                        iCnt = dCardExpansions[sName][sExpansion]
                        for oPhys in aPhysCards:
                            if oPhys not in aPhysCards \
                                    and oPhys.expansion == sExpansion \
                                    and iCnt > 0:
                                aCards.append(oPhys)
                                iCnt -= 1
                                if iCnt == 0:
                                    break
                        if iCnt > 0:
                            dUnknownCards.setdefault((sName, sExpansion), 0)
                            dUnknownCards[(sName, sExpansion)] = iCnt
                except SQLObjectNotFound:
                    for sExpansion in dCardExpansions[sName]:
                        iCnt = dCardExpansions[sName][sExpansion]
                        if iCnt > 0:
                            dUnknownCards.setdefault((sName, sExpansion), 0)
                            dUnknownCards[(sName, sExpansion)] = iCnt
        if dUnknownCards:
            # We need to lookup cards in the physical card view
            if not self._doHandleUnknownPhysCards(dUnknownCards, aCards):
                raise LookupFailed("Lookup of missing cards aborted by the user.")

        return aCards

    def _doHandleUnknownPhysCards(self, dUnknownCards, aPhysCards):
        """Handle unknwon physical cards

           We allow the user to select the correct replacements from the
           Physical Card List
        """

        oUnknownDialog = gtk.Dialog("Unknown Physical cards found", None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oMesgLabel1 = gtk.Label()
        oMesgLabel2 = gtk.Label()

        sMsg1 = "The following card could not be found in the Physical Card List:\n"
        sMsg1 += "\nChoose how to handle these cards?\n"
        sMsg2 = "OK creates the card set, "
        sMsg2 += "Cancel aborts the creation of the card set"

        dReplacement = {}
        for sName, sExpansion in dUnknownCards:
            iCnt = dUnknownCards[(sName, sExpansion)]
            if iCnt <= 0:
                # Should never happen, but ensure robustness against parser
                # errors
                continue
            oBox = gtk.HBox()
            oLabel = gtk.Label("%d copies of %s from expansion %s Not found: Replace with " % (iCnt, sName, sExpansion) )
            oBox.pack_start(oLabel)
            dReplacement[(sName, sExpansion)] = gtk.Label("No Card")
            oBox.pack_start(dReplacement[(sName, sExpansion)])
            oUnknownDialog.vbox.pack_start(oBox)

            oBox = gtk.HButtonBox()
            oButton1 = gtk.Button("Use selected Physical Card")
            oButton2 = gtk.Button("Ignore this Card")
            oButton3 = gtk.Button("Filter Physical Cards with best guess")
            oButton1.connect("clicked", self._set_to_selection,
                    dReplacement[(sName, sExpansion)], 'Physical', iCnt, aPhysCards)
            oButton2.connect("clicked", self._set_ignore,
                    dReplacement[(sName, sExpansion)])
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
            for sName, sExpansion in dUnknownCards:
                sNewName = dReplacement[(sName, sExpansion)].get_text()
                iCnt = dUnknownCards[(sName, sExpansion)]
                if sNewName != "No Card":
                    # Find First physical card that matches this name
                    # that's not in aPhysCards
                    # FIXME: will break with proper expansion support
                    oAbs = AbstractCard.byCanonicalName(sNewName.encode('utf8').lower())
                    aCandPhysCards = PhysicalCard.selectBy(abstractCardID=oAbs.id)
                    for oCard in aCandPhysCards:
                        if oCard not in aPhysCards:
                            if iCnt > 0:
                                iCnt -= 1
                                aPhysCards.append(oCard)
            return True
        else:
            return False


    def _doHandleUnknown(self, dUnknownCards):
        """Handle the list of unknown cards.

           We allow the user to select the correct replacements from the Abstract
           Card List
           """
        oUnknownDialog = gtk.Dialog("Unknown cards found", None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oMesgLabel1 = gtk.Label()
        oMesgLabel2 = gtk.Label()

        sMsg1 = "The following card names could not be found:\n"
        sMsg1 += "\nChoose how to handle these cards?\n"
        sMsg2 = "OK creates the card set, "
        sMsg2 += "Cancel aborts the creation of the card set"

        oMesgLabel1.set_text(sMsg1)
        oUnknownDialog.vbox.pack_start(oMesgLabel1)

        # Fill in the Cards and options
        dReplacement = {}
        for sName in dUnknownCards:
            oBox = gtk.HBox()
            oLabel = gtk.Label("%s is Unknown: Replace with " % sName)
            oBox.pack_start(oLabel)
            dReplacement[sName] = gtk.Label("No Card")
            oBox.pack_start(dReplacement[sName])
            oUnknownDialog.vbox.pack_start(oBox)

            oBox = gtk.HButtonBox()
            oButton1 = gtk.Button("Use selected Abstract Card")
            oButton2 = gtk.Button("Ignore this Card")
            oButton3 = gtk.Button("Filter Abstract Cards with best guess")
            # Count and physical card list don't matter here, so stub values
            oButton1.connect("clicked", self._set_to_selection,
                    dReplacement[sName], 'Abstract', 1, [])
            oButton2.connect("clicked", self._set_ignore,
                    dReplacement[sName])
            oButton3.connect("clicked", self._set_filter, sName, 'Abstract')
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
            # For cards marked as replaced, add them to the Holder
            for sName in dUnknownCards:
                sNewName = dReplacement[sName].get_text()
                if sNewName != "No Card":
                    dUnknownCards[sName] = sNewName
            return True
        else:
            return False

    def _set_to_selection(self, oButton, oRepLabel, sType, iCnt, aPhysCards):
        """Set the replacement to the selected entry"""
        # FIXME: The logic for Physical card sets assumes 
        # that we will be filling in like for like. This will break
        # with expansions (replace 5 of No Expansion with 3 LoB and 
        # 2 Bloodline cases)
        # FIXME: We currently totally ignore the expansion of the selected 
        # card - needs to corrected when GUI supports expansions
        if sType == 'Abstract':
            oModel, aSelection = \
                    self._oAbsCardView.get_selection().get_selected_rows()
        else:
            oModel, aSelection = \
                    self._oPhysCardView.get_selection().get_selected_rows()
        if len(aSelection) != 1:
            oComplaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                gtk.BUTTONS_OK, "This requires that only ONE item be selected")
            oComplaint.connect("response", lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return
        for oPath in aSelection:
            oIter = oModel.get_iter(oPath)
            sNewName = oModel.get_value(oIter, 0)
        if sType == 'Physical' and \
                not self._check_physical_cards(sNewName, iCnt, aPhysCards):
            oComplaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                gtk.BUTTONS_OK, "Not enough copies of ")
            oComplaint.connect("response", lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return
        oRepLabel.hide()
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

    def _set_filter(self, oButton, sName, sType):
        # Set the filter on the Abstract Card List to one the does a
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
        oFilter = CardNameFilter(sFilterString)
        if sType == 'Abstract':
            oView = self._oAbsCardView
        else:
            oView = self._oPhysCardView
        oView.getModel().selectfilter = oFilter
        oView.getModel().applyfilter = True
        oView.getController().getMenu().setApplyFilter(True)
        # Run the filter
        oView.load()

    def _set_ignore(self, oButton, oRepLabel):
        oRepLabel.hide()
        oRepLabel.set_text("No Card")
        oRepLabel.show()
