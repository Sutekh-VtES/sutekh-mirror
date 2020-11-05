# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Create a snapshot of the current card set."""

import datetime

from gi.repository import Gtk

from ...core.BaseTables import PhysicalCardSet
from ...core.CardSetHolder import CardSetHolder
from ..BasePluginManager import BasePlugin
from ..SutekhDialog import do_info_message
from ..GuiCardSetFunctions import get_import_name


class BaseSnapshot(BasePlugin):
    """Creates a snapshot of the card set.

       The snapshot is a copy of the current state of the card set, with the
       date and time appended to the name, and it is a child of the card set.
       """

    dTableVersions = {PhysicalCardSet: (6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Return a Gtk.MenuItem to activate this plugin."""
        oMenuItem = Gtk.MenuItem(label="Take a snapshot of this card set")
        oMenuItem.connect("activate", self.activate)
        return ('Actions', oMenuItem)

    def activate(self, _oWidget):
        """Create the snapshot."""
        oMyCS = self._get_card_set()

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
        self._commit_cards(oNewPCS, oMyCS.cards)
        self._reload_pcs_list()
        sMesg = 'Snapshot <b>%s</b> created' % self._escape(oTempHolder.name)
        do_info_message(sMesg)
