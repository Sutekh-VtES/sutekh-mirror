# SnapshotCardSet.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Create a snapshot of the current card set."""

import gtk
import datetime
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhDialog import do_complaint
from sutekh.gui.GuiCardSetFunctions import get_import_name


class SnapshotCardSet(SutekhPlugin):
    """Creates a snapshot of the card set.

       The snapshot is a copy of the current state of the card set, with the
       date and time appended to the name, and it is a child of the card set.
       """

    dTableVersions = {PhysicalCardSet: (6,)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Return a gtk.MenuItem to activate this plugin."""
        if not self.check_versions() or not self.check_model_type():
            return None
        oMenuItem = gtk.MenuItem("Take a snapshot of this card set")
        oMenuItem.connect("activate", self.activate)
        return ('Actions', oMenuItem)

    def activate(self, _oWidget):
        """Create the snapshot."""
        oMyCS = self.get_card_set()

        sTime = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')

        # ensure we're unique
        oTempHolder = CardSetHolder()
        oTempHolder.name = '%s (%s)' % (oMyCS.name, sTime)
        get_import_name(oTempHolder)
        if not oTempHolder.name:
            return  # user bailed

        oNewPCS = PhysicalCardSet(name=oTempHolder.name, parent=oMyCS)
        oNewPCS.author = oMyCS.author
        oNewPCS.comment = oMyCS.comment
        oNewPCS.annotations = oMyCS.annotations
        oNewPCS.syncUpdate()

        # Copy the cards
        for oCard in oMyCS.cards:
            # pylint: disable-msg=E1101, E1103
            # SQLObject confuses pylint
            oNewPCS.addPhysicalCard(oCard)
            oNewPCS.syncUpdate()

        self.reload_pcs_list()
        sMesg = 'Snapshot <b>%s</b> created' % self.escape(oTempHolder.name)
        do_complaint(sMesg, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, True)


plugin = SnapshotCardSet
