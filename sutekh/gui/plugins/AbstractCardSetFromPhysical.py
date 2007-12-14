# AbstractCardSetFromPhysical.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import do_complaint_error

class AbstractCardSetFromPhysical(CardListPlugin):
    """Create a equivilant Abstract Card Set from a given
       Physical Card Set."""
    dTableVersions = { AbstractCardSet : [2,3]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Generate a Abstract Card Set")
        iDF.connect("activate", self.activate)

        return iDF

    def get_desired_menu(self):
        return "Plugins"

    def activate(self,oWidget):
        self.createAbsCardSet()

    def createAbsCardSet(self):
        oPC = PhysicalCardSet.byName(self.view.sSetName)
        oDlg = CreateCardSetDialog(self.parent,"AbstractCardSet",oPC.author,oPC.comment)
        oDlg.run()

        (sName,sAuthor,sDesc) = oDlg.get_data()

        if sName is not None:
            oNameList = AbstractCardSet.selectBy(name=sName)
            if oNameList.count() != 0:
                do_complaint_error("Chosen Abstract Card Set already exists")
                return
            nA = AbstractCardSet(name=sName)
            nA.author = sAuthor
            nA.comment = sDesc
            nA.syncUpdate()
            # Copy the cards across
            for oCard in self.model.getCardIterator(None):
                nA.addAbstractCard(oCard.abstractCardID)

            self.open_acs(sName)

plugin = AbstractCardSetFromPhysical
