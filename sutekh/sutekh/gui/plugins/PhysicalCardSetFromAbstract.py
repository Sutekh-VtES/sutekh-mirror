# PhysicalCardSetFromAbstract.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import PhysicalCardSet, AbstractCardSet, PhysicalCard
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.PluginManager import CardListPlugin

class PhysicalCardSetFromAbstract(CardListPlugin):
    """Create a (as far as possible) equivilant Physical Card Set
       from a given Abstract Card Set.
       
       - Ignores Cards which don't exist in Physical Cards (but notifies the user)
       - Has an option to import the cards into your card collection before creating the Physical Card Set."""

    dTableVersions = {"PhysicalCardSet" : [2,3], "PhysicalCard" : [1,2] }
    aModelsSupported = ["AbstractCardSet"]

    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Generate a Physical Card Set")
        iDF.connect("activate", self.activate)
        return iDF

    def getDesiredMenu(self):
        return "CardSet"

    def activate(self,oWidget):
        self.createPhysCardSet()

    def createPhysCardSet(self):
        parent = self.view.getWindow()
        oAC = AbstractCardSet.byName(self.view.sSetName)

        oDlg = CreateCardSetDialog(parent,"PhysicalCardSet",oAC.author,oAC.comment)
        oImport = gtk.CheckButton("Add cards to collection.")
        oDlg.vbox.pack_start(oImport)
        oDlg.show_all()
        oDlg.run()

        (sName, sAuthor, sDesc) = oDlg.getName()
        if sName is None:
            return

        aNameList = PhysicalCardSet.selectBy(name=sName)
        if aNameList.count() != 0:
            Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                          gtk.BUTTONS_CLOSE,
                                          "Chosen Physical Card Set already exists")
            Complaint.run()
            Complaint.destroy()
            return

        nP = PhysicalCardSet(name=sName)
        nP.author=sAuthor
        nP.comment=sDesc
        nP.syncUpdate()

        # Add cards to physical card collection if requested
        if oImport.get_active():
            for oCard in self.model.getCardIterator(None):
                PhysicalCard(abstractCard=oCard)

        # Populate the new physical card set
        aMissingCards = []
        for oCard in self.model.getCardIterator(None):
            oPhysCards = PhysicalCard.selectBy(abstractCardID=oCard.id)
            for oPC in oPhysCards:
                if oPC not in nP.cards:
                    nP.addPhysicalCard(oPC.id)
                    break
            else:
                aMissingCards.append(oCard)

        parent.getManager().reloadCardSetLists()

        if aMissingCards:
            sMsg = "The following cards were not added to the physical card set " \
                   "because they are not present in your card collection:\n\n" \
                   + "\n".join([oC.name for oC in aMissingCards])
            Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                          gtk.BUTTONS_CLOSE,sMsg)
            Complaint.run()
            Complaint.destroy()

plugin = PhysicalCardSetFromAbstract
