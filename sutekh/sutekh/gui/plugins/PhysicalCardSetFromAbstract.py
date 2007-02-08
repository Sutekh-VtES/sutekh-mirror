# PhysicalCardSetFromAbstract.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from gui.CreateCardSetDialog import CreateCardSetDialog
from gui.PluginManager import CardListPlugin

class PhysicalCardSetFromAbstract(CardListPlugin):
    """Create a (as far as possible) equivilant Physical Card Set
       from a given Abstract Card Set.
       Ignores Cards which don't exist in Physical Cards"""
       #Q: How should the user be informed of missing cards?
    dTableVersions = {"PhysicalCardSet" : [2]}
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
        oAC=AbstractCardSet.byName(self.view.sSetName)
        oDlg = CreateCardSetDialog(parent,"PhysicalCardSet",oAC.author,oAC.comment)
        oDlg.run()
        (sName, sAuthor, sDesc) = oDlg.getName()
        if sName is not None:
            NameList = PhysicalCardSet.selectBy(name=sName)
            if NameList.count()!=0:
                Complaint=gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE,"Chosen Physical Card Set already exists")
                Complaint.run()
                Complaint.destroy()
                return
            nP=PhysicalCardSet(name=sName)
            nP.author=sAuthor
            nP.comment=sComment
            nP.syncUpdate()
            # Copy the cards across
            for oCard in self.model.getCardIterator(None):
                oPhysCards=PhysicalCard.selectBy(abstractCardID=oCard.id)
                if oPhysCards.count() > 0:
                    for oPC in oPhysCards:
                        if oPC not in nP.cards:
                            nP.addPhysicalCard(oPC.id)
                            break

plugin = PhysicalCardSetFromAbstract
