# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008, 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to standard writers"""

from gi.repository import Gtk
from ...core.BaseTables import PhysicalCardSet
from ..BasePluginManager import BasePlugin
from ..GuiCardSetFunctions import export_cs


class BaseCardSetExport(BasePlugin):
    """Provides a dialog for selecting a filename, then calls on
       the appropriate writer to produce the required output."""
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    # Subclasses should fill this in as needed
    EXPORTERS = {
        # sKey : (writer, menu name, extension, [filter name,
        #         filter pattern], [filter name, pattern])
        # Filter name & pattern are optional, and default to
        # 'Text files', ['*.txt'] if not present
        # filter pattern must be a list of patterns for the given name
        # Extension is appended to suggested filename with a '.' between
        # the filename and the extension, so should not include an initial '.'
    }

    def get_menu_item(self):
        """Register with the 'Export Card Set' Menu"""
        aMenuItems = []
        for sKey, tInfo in self.EXPORTERS.items():
            sMenuText = tInfo[1]
            oExport = Gtk.MenuItem(label=sMenuText)
            oExport.connect("activate", self.make_dialog, sKey)
            aMenuItems.append(('Export Card Set', oExport))
        return aMenuItems

    def make_dialog(self, _oWidget, sKey):
        """Create the dialog"""
        oCardSet = self._get_card_set()
        if not oCardSet:
            return
        tInfo = self.EXPORTERS[sKey]
        aPatterns = None
        if len(tInfo) > 3:
            aPatterns = zip(tInfo[3::2], tInfo[4::2])
        export_cs(oCardSet, tInfo[0], self.parent, tInfo[2], aPatterns)
