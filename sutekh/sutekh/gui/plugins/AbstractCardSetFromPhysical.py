# AbstractCardSetFromPhysical.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import *
from gui.CreateCardSetDialog import CreateCardSetDialog
from gui.PluginManager import CardListPlugin

class AbstractCardSetFromPhysical(CardListPlugin):
    """Create a equivilant Abstract Card Set from a given
       Physical Card Set."""
    dTableVersions={}
    aModelsSupported = ['PhysicalCardSet']
    def getMenuItem(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None
        iDF = gtk.MenuItem("Generate a Abstract Card Set")
        iDF.connect("activate", self.activate)

        return iDF

    def activate(self,oWidget):
        self.createAbsCardSet()

    def createAbsCardSet(self):
        parent = self.view.getWindow()
        oDlg = CreateCardSetDialog(parent,"AbstractCardSet")
        oDlg.run()
        sName = oDlg.getName()
        if sName is not None:
            NameList = AbstractCardSet.selectBy(name=sName)
            if NameList.count()!=0:
                Complaint=gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE,"Chosen Abstract Card Set already exists")
                Complaint.run()
                Complaint.destroy()
                return
            nA=AbstractCardSet(name=sName)
            # Copy the cards across
            for oCard in self.model.getCardIterator(None):
                nA.addAbstractCard(oCard.abstractCardID)

plugin = AbstractCardSetFromPhysical
