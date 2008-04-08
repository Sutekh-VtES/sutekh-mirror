# AbstractCardSetFromPhysical.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Create an Abstract Card Set with the same cards as the existing
   Physical card Set"""

import gtk
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import do_complaint_error

class AbstractCardSetFromPhysical(CardListPlugin):
    """Create a equivilant Abstract Card Set from a given
       Physical Card Set."""
    dTableVersions = { AbstractCardSet : [2, 3]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register with the 'Plugins' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oGenACS = gtk.MenuItem("Generate a Abstract Card Set")
        oGenACS.connect("activate", self.activate)

        return ('Plugins', oGenACS)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def activate(self, oWidget):
        """Handle the response from the menu and create the card set"""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        oPC = PhysicalCardSet.byName(self.view.sSetName)
        oDlg = CreateCardSetDialog(self.parent, "AbstractCardSet", oPC.author,
                oPC.comment)
        oDlg.run()

        (sName, sAuthor, sDesc) = oDlg.get_data()

        if sName is not None:
            oNameList = AbstractCardSet.selectBy(name=sName)
            if oNameList.count() != 0:
                do_complaint_error("Chosen Abstract Card Set already exists")
                return
            oNewAC = AbstractCardSet(name=sName)
            oNewAC.author = sAuthor
            oNewAC.comment = sDesc
            oNewAC.syncUpdate()
            # Copy the cards across
            for oCard in self.model.getCardIterator(None):
                oNewAC.addAbstractCard(oCard.abstractCardID)

            self.open_acs(sName)

# pylint: disable-msg=C0103
# accept plugin name
plugin = AbstractCardSetFromPhysical
