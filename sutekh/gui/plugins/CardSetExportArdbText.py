# CardSetExportArdbText.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to ARDB's XML format"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.SutekhUtility import safe_filename

class CardSetExportArdbText(CardListPlugin):
    """Provides a dialog for selecting a filename, then calls on
       WriteArdbText to produce the required output."""
    dTableVersions = { PhysicalCardSet: [2, 3, 4, 5]}
    aModelsSupported = [PhysicalCardSet]

    def get_menu_item(self):
        """Register with the 'Export Card Set' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oExport = gtk.MenuItem("Export to ARDB Text")
        oExport.connect("activate", self.make_dialog)
        return ('Export Card Set', oExport)

    # pylint: disable-msg=W0613
    # oWidget has to be here, although it's unused
    def make_dialog(self, oWidget):
        """Create the dialog"""
        oDlg = ExportDialog("Choose FileName for Exported CardSet",
                self.parent, '%s.txt' % safe_filename(self.view.sSetName))
        oDlg.add_filter_with_pattern('Text Files', ['*.txt'])
        oDlg.run()
        self.handle_response(oDlg.get_name())

    # pylint: enable-msg=W0613

    def handle_response(self, sFileName):
        """Handle the users response. Write the text output to file."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        if sFileName is not None:
            oCardSet = self.get_card_set()
            if not oCardSet:
                return
            oWriter = WriteArdbText()
            fOut = file(sFileName,"w")
            oWriter.write(fOut, self.view.sSetName, oCardSet.author,
                    oCardSet.comment, self.get_all_cards())
            fOut.close()

# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetExportArdbText
