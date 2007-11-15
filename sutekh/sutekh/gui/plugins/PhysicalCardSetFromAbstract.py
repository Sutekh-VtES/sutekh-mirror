# PhysicalCardSetFromAbstract.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, PhysicalCard, \
                                      IAbstractCard
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.PluginManager import CardListPlugin

class PhysicalCardSetFromAbstract(CardListPlugin):
    """Create a (as far as possible) equivilant Physical Card Set
       from a given Abstract Card Set.

       - Ignores Cards which don't exist in Physical Cards (but notifies the user)
       - Has an option to import the cards into your card collection before creating the Physical Card Set."""

    dTableVersions = { PhysicalCardSet: [2,3], PhysicalCard: [1,2] }
    aModelsSupported = [AbstractCardSet]

    def get_menu_item(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None
        iDF = gtk.MenuItem("Generate a Physical Card Set")
        iDF.connect("activate", self.activate)
        return iDF

    def get_desired_menu(self):
        return "CardSet"

    def activate(self,oWidget):
        self.createPhysCardSet()

    def createPhysCardSet(self):
        oAC = AbstractCardSet.byName(self.view.sSetName)

        oDlg = CreateCardSetDialog(self.parent,"PhysicalCardSet",oAC.author,oAC.comment)
        oImport = gtk.CheckButton("Add cards to collection.")
        oDlg.vbox.pack_start(oImport)
        oDlg.show_all()
        oDlg.run()

        (sName, sAuthor, sDesc) = oDlg.get_data()
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
        nP.author = sAuthor
        nP.comment = sDesc
        nP.syncUpdate()

        # Add cards to physical card collection if requested
        if oImport.get_active():
            for oCard in self.model.getCardIterator(None):
                oAC = IAbstractCard(oCard)
                PhysicalCard(abstractCard=oAC,expansion=None)
            self.reload_all()

        # Populate the new physical card set
        aMissingCards = []
        for oCard in self.model.getCardIterator(None):
            oACard = IAbstractCard(oCard)
            oPhysCards = PhysicalCard.selectBy(abstractCardID=oACard.id)
            for oPC in oPhysCards:
                if oPC not in nP.cards:
                    nP.addPhysicalCard(oPC.id)
                    break
            else:
                aMissingCards.append(oACard)

        self.open_pcs(sName)

        if aMissingCards:
            sMsg = "The following cards were not added to the physical card set " \
                "because they are not present in your card collection:\n\n" \
                + "\n".join([oC.name for oC in aMissingCards])
            Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE,sMsg)
            Complaint.run()
            Complaint.destroy()

plugin = PhysicalCardSetFromAbstract
