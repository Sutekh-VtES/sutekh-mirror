# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to CSV format"""

from gi.repository import Gtk
from ...core.BaseTables import PhysicalCardSet
from ...io.WriteCSV import WriteCSV
from ...Utility import safe_filename
from ..BasePluginManager import BasePlugin
from ..SutekhFileWidget import ExportDialog
from ..GuiCardSetFunctions import write_cs_to_file


class BaseExportCSV(BasePlugin):
    """Provides a dialog for selecting a filename, then calls on
       WriteCSV to produce the required output."""
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Register on the 'Export Card Set' Menu"""
        oExport = Gtk.MenuItem(label="Export to CSV")
        oExport.connect("activate", self.make_dialog)
        return ('Export Card Set', oExport)

    def make_dialog(self, _oWidget):
        """Create the dialog"""
        oDlg = ExportDialog("Choose FileName for Exported CardSet",
                            self.parent,
                            '%s.csv' % safe_filename(self.view.sSetName))
        oDlg.add_filter_with_pattern('CSV Files', ['*.xml'])
        oIncHeader = Gtk.CheckButton("Include Column Headers")
        oIncHeader.set_active(True)
        oDlg.vbox.pack_start(oIncHeader, False, True, 0)
        oIncExpansion = Gtk.CheckButton("Include Expansions")
        oIncExpansion.set_active(True)
        oDlg.vbox.pack_start(oIncExpansion, False, True, 0)
        oDlg.show_all()
        oDlg.run()

        self.handle_response(oDlg.get_name(), oIncHeader.get_active(),
                             oIncExpansion.get_active())

    def handle_response(self, sFileName, bIncHeader, bIncExpansion):
        """Handle the users response. Write the CSV output to file."""
        if sFileName is not None:
            oCardSet = self._get_card_set()
            if not oCardSet:
                return
            oWriter = WriteCSV(bIncHeader, bIncExpansion)
            write_cs_to_file(oCardSet, oWriter, sFileName)
