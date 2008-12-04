# CardSetExportFELDB.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to ELDB's deck & inventory formats"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.io.WriteELDBInventory import WriteELDBInventory
from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
from sutekh.SutekhUtility import safe_filename

class CardSetExportFELDB(CardListPlugin):
    """Provides a dialog for selecting a filename, then calls on
       WriteELDB* to produce the required output."""
    dTableVersions = { PhysicalCardSet: [5]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register on the 'Export Card Set' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oExport = gtk.MenuItem("Export to FELDB file")
        oExport.connect("activate", self.make_dialog)
        return ('Export Card Set', oExport)

    # pylint: disable-msg=W0613
    # oWidget has to be here, although it's unused
    def make_dialog(self, oWidget):
        """Create the dialog"""
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDlg = ExportDialog("Choose FileName for Exported CardSet",
                self.parent, '%s_ELDB.eld' % safe_filename(self.view.sSetName))
        oDlg.add_filter_with_pattern('ELD Files', ['*.eld'])
        oDlg.add_filter_with_pattern('CSV Files', ['*.csv'])
        oFirstBut = gtk.RadioButton(None, 'ELDB Deck File', False)
        oDlg.vbox.pack_start(oFirstBut, expand=False)
        oSecondBut = gtk.RadioButton(oFirstBut, 'ELDB Inventory CSV File')
        oDlg.vbox.pack_start(oSecondBut, expand=False)
        oDlg.show_all()
        oDlg.run()
        self.handle_response(oDlg.get_name(), oFirstBut)

    # pylint: enable-msg=W0613

    def handle_response(self, sFileName, oFirstBut):
        """Handle the users response. Write the output to file."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        if sFileName is not None:
            oCardSet = self.get_card_set()
            if not oCardSet:
                return
            fOut = file(sFileName,"w")
            if oFirstBut.get_active():
                oWriter = WriteELDBDeckFile()
                oWriter.write(fOut, oCardSet)
            else:
                oWriter = WriteELDBInventory()
                oWriter.write(fOut, oCardSet)
            fOut.close()

# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetExportFELDB
