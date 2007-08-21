# ACSFromFilter.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import urllib2
from sutekh.ELDBHTMLParser import ELDBHTMLParser
from sutekh.SutekhObjects import AbstractCardSet
from sutekh.Filters import CardNameFilter
from sutekh.gui.PluginManager import CardListPlugin

class ACSFromELDBHTML(CardListPlugin):
    dTableVersions = { "AbstractCardSet" : [2,3]}
    aModelsSupported = ["AbstractCard"]

    def __init__(self,*args,**kws):
        super(ACSFromELDBHTML,self).__init__(*args,**kws)

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Abstract Card Set From ELDB HTML")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "Plugin"

    def activate(self,oWidget):
        oDlg = self.makeDialog()
        oDlg.run()

    def makeDialog(self):
        parent = self.view.getWindow()

        self.oDlg = gtk.Dialog("Choose ELDB HTML File",None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                 gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.oDlg.vbox.pack_start(gtk.Label("URL:"),expand=False)

        self.oUri = gtk.Entry(150)
        self.oUri.connect("activate", self.handleResponse, gtk.RESPONSE_OK)
        self.oDlg.vbox.pack_start(self.oUri,expand=False)

        self.oDlg.vbox.pack_start(gtk.Label("OR"),expand=False)

        self.oFileChooser = gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oDlg.vbox.pack_start(self.oFileChooser)

        self.oDlg.connect("response", self.handleResponse)
        self.oDlg.set_size_request(400,300)
        self.oDlg.show_all()

        return self.oDlg

    def handleResponse(self,oWidget,oResponse):
        if oResponse == gtk.RESPONSE_OK:
            sUri = self.oUri.get_text().strip()
            sFile = self.oFileChooser.get_filename()
            if sUri:
                self.makeACSFromUri(sUri)
            elif sFile:
                self.makeACSFromFile(sFile)

        self.oDlg.destroy()

    def makeACSFromUri(self,sUri):
        fIn = urllib2.urlopen(sUri)
        try:
            self.makeACS(fIn)
        finally:
            fIn.close()

    def makeACSFromFile(self,sFile):
        fIn = file(sFile,"rb")
        try:
            self.makeACS(fIn)
        finally:
            fIn.close()

    def makeACS(self,fIn):
        oP = ELDBHTMLParser()
        for sLine in fIn:
            oP.feed(sLine)
        oHolder = oP.holder()

        # Check ACS Doesn't Exist
        if AbstractCardSet.selectBy(name=oHolder.name).count() != 0:
            sMsg = "Abstract Card Set %s already exists." % oHolder.name
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_CLOSE, sMsg)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        # Warn about unparse-able cards
        aUnknown = oHolder.unknownCards()
        if aUnknown:
            bContinue = self.doHandleUnknown(aUnknown,oHolder)
#            sMsg = "The following card names could not be found:\n"
#            sMsg += "\n".join(["%dx %s" % (iCnt, sName) for (iCnt, sName) in aUnknown])
#            sMsg += "\nCreate card set anyway?"
#            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
#                                           gtk.BUTTONS_OK_CANCEL, sMsg)
#            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
#            bContinue = oComplaint.run() != gtk.RESPONSE_CANCEL
            if not bContinue:
                return

        # Create ACS
        try:
            oHolder.createACS()
        except RuntimeError, e:
            sMsg = "Creating the card set failed with the following error:\n"
            sMsg += str(e) + "\n"
            sMsg += "The file is probably not in the format the ELDB Parser expects\n"
            sMsg += "Aborting"
            oComplaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_OK, sMsg)
            oComplaint.connect("response",lambda oW, oResp: oW.destroy())
            oComplaint.run()
            return

        parent = self.view.getWindow()
        parent.getManager().reloadCardSetLists()

    def doHandleUnknown(self,aUnknownCards,oHolder):
        """Handle the list of unknown cards - we allow the user to
           select the correct replacements from the Abstract Card List"""

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
        for iCnt,sName in aUnknownCards:
            oBox = gtk.HBox()
            oLabel = gtk.Label(str(iCnt) + "x %s is Unknown: Replace with " % sName)
            oBox.pack_start(oLabel)
            dReplacement[sName] = gtk.Label("No Card")
            oBox.pack_start(dReplacement[sName])
            oUnknownDialog.vbox.pack_start(oBox)

            oBox = gtk.HButtonBox()
            Button1 = gtk.Button("Use selected Abstract Card")
            Button2 = gtk.Button("Ignore this Card")
            Button3 = gtk.Button("Filter Abstract Cards with best guess")
            Button1.connect("clicked",self.setToSelection,dReplacement[sName])
            Button2.connect("clicked",self.setIgnore,dReplacement[sName])
            Button3.connect("clicked",self.setFilter,sName)
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
            for iCnt,sName in aUnknownCards:
                sNewName = dReplacement[sName].get_text()
                if sNewName != "No Card":
                    oHolder.addCards(iCnt,sNewName)
            return True
        else:
            return False

    def setToSelection(self,oButton,oRepLabel):
        oModel,aSelection = self.view.get_selection().get_selected_rows()
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

    def setFilter(self,oButton,sName):
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
        self.view.getModel().selectfilter = oFilter
        self.view.getModel().applyfilter = True
        # Run the filter
        self.view.load()
        pass

    def setIgnore(self,oButton,oRepLabel):
        oRepLabel.hide()
        oRepLabel.set_text("No Card")
        oRepLabel.show()

plugin = ACSFromELDBHTML
