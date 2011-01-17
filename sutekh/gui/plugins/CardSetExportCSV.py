# CardSetExportCSV.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to CSV format"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteCSV import WriteCSV
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.SutekhUtility import safe_filename


class CardSetExportCSV(SutekhPlugin):
    """Provides a dialog for selecting a filename, then calls on
       WriteCSV to produce the required output."""
    dTableVersions = {PhysicalCardSet: (4, 5, 6)}
    aModelsSupported = (PhysicalCardSet,)

    def get_menu_item(self):
        """Register on the 'Export Card Set' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oExport = gtk.MenuItem("Export to CSV")
        oExport.connect("activate", self.make_dialog)
        return ('Export Card Set', oExport)

    def make_dialog(self, _oWidget):
        """Create the dialog"""
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDlg = ExportDialog("Choose FileName for Exported CardSet",
                self.parent, '%s.csv' % safe_filename(self.view.sSetName))
        oDlg.add_filter_with_pattern('CSV Files', ['*.xml'])
        oIncHeader = gtk.CheckButton("Include Column Headers")
        oIncHeader.set_active(True)
        oDlg.vbox.pack_start(oIncHeader, expand=False)
        oIncExpansion = gtk.CheckButton("Include Expansions")
        oIncExpansion.set_active(True)
        oDlg.vbox.pack_start(oIncExpansion, expand=False)
        oDlg.show_all()
        oDlg.run()

        self.handle_response(oDlg.get_name(), oIncHeader.get_active(),
                oIncExpansion.get_active())

    def handle_response(self, sFileName, bIncHeader, bIncExpansion):
        """Handle the users response. Write the CSV output to file."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        if sFileName is not None:
            oCardSet = self.get_card_set()
            if not oCardSet:
                return
            fOut = file(sFileName, "w")
            oWriter = WriteCSV(bIncHeader, bIncExpansion)
            oWriter.write(fOut, CardSetWrapper(oCardSet))
            fOut.close()


plugin = CardSetExportCSV
