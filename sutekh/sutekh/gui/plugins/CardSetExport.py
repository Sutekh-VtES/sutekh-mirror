# CardSetExport.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008, 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to standard writers"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.io.WriteJOL import WriteJOL
from sutekh.io.WriteLackeyCCG import WriteLackeyCCG
from sutekh.io.WriteArdbXML import WriteArdbXML
from sutekh.io.WriteArdbInvXML import WriteArdbInvXML
from sutekh.io.WriteELDBInventory import WriteELDBInventory
from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.io.WriteVEKNForum import WriteVEKNForum
from sutekh.SutekhUtility import safe_filename


class CardSetExport(SutekhPlugin):
    """Provides a dialog for selecting a filename, then calls on
       the appropriate writer to produce the required output."""
    dTableVersions = {PhysicalCardSet: (4, 5, 6)}
    aModelsSupported = (PhysicalCardSet,)

    _dExporters = {
            # sKey : (writer, menu name, extension, [filter name,
            #         filter pattern], [filter name, pattern])
            # Filter name & pattern are optional, and default to
            # 'Text files', '*.txt' if not present
            # Extension is directly appended to suggested filename,
            # so should include an initial . if appropriate
            'JOL': (WriteJOL, 'Export to JOL format', '.jol.txt'),
            'Lackey': (WriteLackeyCCG, 'Export to Lackey CCG format',
                '.lackey.txt'),
            'ARDB Text': (WriteArdbText, 'Export to ARDB Text', '.ardb.txt'),
            'vekn.net': (WriteVEKNForum,
                'BBcode output for the V:EKN Forums', '.vekn.txt'),
            'FELDB Inv': (WriteELDBInventory,
                'Export to ELDB CSV Inventory File', '.eldb.csv', 'CSV Files',
                ['*.csv']),
            'FELDB Deck': (WriteELDBDeckFile, 'Export to ELDB ELD Deck File',
                '.eldb.eld', 'ELD Files', ['*.eld']),
            'ARDB Inv': (WriteArdbInvXML, 'Export to ARDB Inventory XML File',
                '.inv.ardb.xml', 'XML Files', ['*.xml']),
            'ARDB Deck': (WriteArdbXML, 'Export to ARDB Deck XML File',
                '.ardb.xml', 'XML Files', ['*.xml']),
            }

    def get_menu_item(self):
        """Register with the 'Export Card Set' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        aMenuItems = []
        for sKey, tInfo in self._dExporters.iteritems():
            sMenuText = tInfo[1]
            oExport = gtk.MenuItem(sMenuText)
            oExport.connect("activate", self.make_dialog, sKey)
            aMenuItems.append(('Export Card Set', oExport))
        return aMenuItems

    def make_dialog(self, _oWidget, sKey):
        """Create the dialog"""
        tInfo = self._dExporters[sKey]
        sSuggestedFileName = '%s%s' % (safe_filename(self.view.sSetName),
            tInfo[2])
        oDlg = ExportDialog("Choose FileName for Exported CardSet",
                self.parent, sSuggestedFileName)
        if len(tInfo) > 3:
            for sName, aPattern in zip(tInfo[3::2], tInfo[4::2]):
                oDlg.add_filter_with_pattern(sName, aPattern)
        else:
            oDlg.add_filter_with_pattern('Text Files', ['*.txt'])
        oDlg.run()
        self.handle_response(oDlg.get_name(), tInfo[0])

    def handle_response(self, sFileName, cWriter):
        """Handle the users response. Write the text output to file."""
        if sFileName is not None:
            oCardSet = self.get_card_set()
            if not oCardSet:
                return
            oWriter = cWriter()
            fOut = file(sFileName, "w")
            oWriter.write(fOut, CardSetWrapper(oCardSet))
            fOut.close()


plugin = CardSetExport
