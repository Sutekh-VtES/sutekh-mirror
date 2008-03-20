# PhysicalCardSetFromAbstract.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"Convert an Abstract Card Set to a Physical Card Set"

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, \
        PhysicalCard, IAbstractCard
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.PluginManager import CardListPlugin

class PhysicalCardSetFromAbstract(CardListPlugin):
    """Create a (as far as possible) equivilant Physical Card Set
       from a given Abstract Card Set.

       - Ignores Cards which don't exist in Physical Cards
         (but notifies the user)
       - Has an option to import the cards into your card collection
         before creating the Physical Card Set."""

    dTableVersions = { PhysicalCardSet: [2, 3, 4], PhysicalCard: [1, 2] }
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
        "Override base class. Register on the plugins menu"
        return "Plugins"

    # pylint: disable-msg=W0613
    # oWidget required by gtk function signature
    def activate(self, oWidget):
        "Handle menu activation"
        self.create_physical_card_set()
    # pylint: enable-msg=W0613

    def create_physical_card_set(self):
        "Create the actual physical card"
        # pylint: disable-msg=E1101
        # pylint misses AbstractCardSet methods
        oAC = AbstractCardSet.byName(self.view.sSetName)

        oDlg = CreateCardSetDialog(self.parent, "PhysicalCardSet", oAC.author,
                oAC.comment)
        oImport = gtk.CheckButton("Add cards to collection.")
        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        oDlg.vbox.pack_start(oImport)
        oDlg.show_all()
        oDlg.run()
        # pylint: enable-msg=E1101

        (sName, sAuthor, sDesc) = oDlg.get_data()
        if sName is None:
            return

        aNameList = PhysicalCardSet.selectBy(name=sName)
        if aNameList.count() != 0:
            do_complaint_error("Chosen Physical Card Set already exists")
            return

        oNewPCS = PhysicalCardSet(name=sName)
        oNewPCS.author = sAuthor
        oNewPCS.comment = sDesc
        oNewPCS.syncUpdate()

        # Add cards to physical card collection if requested
        if oImport.get_active():
            for oCard in self.model.getCardIterator(None):
                # pylint: disable-msg=E1101
                # pylint misses IAbstractCard methods
                oAC = IAbstractCard(oCard)
                PhysicalCard(abstractCard=oAC, expansion=None)
            self.reload_all()

        # Populate the new physical card set
        aMissingCards = []
        for oCard in self.model.getCardIterator(None):
            oACard = IAbstractCard(oCard)
            # pylint: disable-msg=E1101
            # pylint misses AbstractCard methods (id)
            oPhysCards = PhysicalCard.selectBy(abstractCardID=oACard.id)
            for oPC in oPhysCards:
                if oPC not in oNewPCS.cards:
                    # pylint: disable-msg=E1101
                    # pylint misses PhysicalCardSet methods
                    oNewPCS.addPhysicalCard(oPC.id)
                    break
            else:
                aMissingCards.append(oACard)

        self.open_pcs(sName)

        if aMissingCards:
            do_complaint_error("The following cards were not added to the" 
                    " physical card set because they are not present in your" 
                    " card collection: %s\n\n" % 
                    "\n".join([oC.name for oC in aMissingCards]))

# pylint: disable-msg=C0103
# accept plugin name
plugin = PhysicalCardSetFromAbstract
