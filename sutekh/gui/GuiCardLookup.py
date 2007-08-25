# CardLookup.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Lookup AbstractCards for a list of card names, presenting the user with a GUI
   to pick unknown cards from.
   """

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.SutekhObjects import AbstractCard
from sutekh.CardLookup import AbstractCardLookup, LookupFailed
from sutekh.Filters import CardNameFilter

class GuiLookup(AbstractCardLookup):
    """Lookup AbstractCards. Use the user as the AI if a simple lookup fails.
       """

    def __init__(self,oAbsCardView):
        # FIXME: Should this create an abstract card list view inside the
        #        dialog? For times when the abstract card list isn't visible?
        self._oAbsCardView = oAbsCardView

    def lookup(self,aNames):
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

    def _doHandleUnknown(self,dUnknownCards):
        """Handle the list of unknown cards.
        
           We allow the user to select the correct replacements from the Abstract
           Card List
           """
        oUnknownDialog = gtk.Dialog("Unknown cards found",None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oMesgLabel1 = gtk.Label()
        oMesgLabel2 = gtk.Label()

        sMsg1 = "The following card names could not be found:\n"
        sMsg1 += "\nChoose how to handle these cards?\n"
        sMsg2 = "OK creates the card set, Cancel aborts the creation of the card set"

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
            Button1 = gtk.Button("Use selected Abstract Card")
            Button2 = gtk.Button("Ignore this Card")
            Button3 = gtk.Button("Filter Abstract Cards with best guess")
            Button1.connect("clicked",self._setToSelection,dReplacement[sName])
            Button2.connect("clicked",self._setIgnore,dReplacement[sName])
            Button3.connect("clicked",self._setFilter,sName)
            oBox.pack_start(Button1)
            oBox.pack_start(Button2)
            oBox.pack_start(Button3)
            oUnknownDialog.vbox.pack_start(oBox)

        oMesgLabel2.set_text(sMsg2)

        oUnknownDialog.vbox.pack_start(oMesgLabel2)
        oUnknownDialog.vbox.show_all()

        response = oUnknownDialog.run()

        oUnknownDialog.destroy()

        if response == gtk.RESPONSE_OK:
            # For cards marked as replaced, add them to the Holder
            for sName in dUnknownCards:
                sNewName = dReplacement[sName].get_text()
                if sNewName != "No Card":
                    dUnknownCards[sName] = sNewName
            return True
        else:
            return False

    def _setToSelection(self,oButton,oRepLabel):
        oModel, aSelection = self._oAbsCardView.get_selection().get_selected_rows()
        if len(aSelection) != 1:
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                gtk.BUTTONS_OK, "This requires that only ONE item be selected")
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return
        for oPath in aSelection:
            oIter = oModel.get_iter(oPath)
            sNewName = oModel.get_value(oIter,0)
        oRepLabel.hide()
        oRepLabel.set_text(sNewName)
        oRepLabel.show()

    def _setFilter(self,oButton,sName):
        # Set the filter on the Abstract Card List to one the does a
        # Best guess search
        sFilterString = ' '+sName.lower()+' '
        # Kill the's in the string
        sFilterString = sFilterString.replace(' the ','')
        # Kill commas, as possible issues
        sFilterString = sFilterString.replace(',','')
        # Wildcard spaces
        sFilterString = sFilterString.replace(' ','%').lower()
        # Stolen semi-concept from soundex - replace vowels with wildcards
        # Should these be %'s ??
        # (Should at least handle the Rotscheck variation as it stands)
        sFilterString = sFilterString.replace('a','_')
        sFilterString = sFilterString.replace('e','_')
        sFilterString = sFilterString.replace('i','_')
        sFilterString = sFilterString.replace('o','_')
        sFilterString = sFilterString.replace('u','_')
        oFilter = CardNameFilter(sFilterString)
        self._oAbsCardView.getModel().selectfilter = oFilter
        self._oAbsCardView.getModel().applyfilter = True
        # Run the filter
        self._oAbsCardView.load()
        pass

    def _setIgnore(self,oButton,oRepLabel):
        oRepLabel.hide()
        oRepLabel.set_text("No Card")
        oRepLabel.show()
