# CardSetExportArdbText.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to ARDB's XML format"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, \
        IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.SutekhFileWidget import SutekhFileWidget
from sutekh.io.WriteArdbText import WriteArdbText

class CardSetExportArdbText(CardListPlugin):
    """Provides a dialog for selecting a filename, then calls on
       WriteArdbText to produce the required output."""
    dTableVersions = { AbstractCardSet: [2, 3],
                       PhysicalCardSet: [2, 3, 4]}
    aModelsSupported = [AbstractCardSet, PhysicalCardSet]

    def get_menu_item(self):
        """Register with the 'Plugins' Menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oExport = gtk.MenuItem("Export Card Set to ARDB Text")
        oExport.connect("activate", self.make_dialog)
        return ('Plugins', oExport)

    # pylint: disable-msg=W0613, W0201
    # W0613 - oWidget has to be here, although it's unused
    # W0201 - we define things here, rather than __init__, since this
    # is the plugin's entry point
    def make_dialog(self, oWidget):
        """Create the dialog"""
        self.oDlg = SutekhDialog("Choose FileName for Exported CardSet",
                self.parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oFileChooser = SutekhFileWidget(self.parent,
                gtk.FILE_CHOOSER_ACTION_SAVE)
        self.oFileChooser.set_do_overwrite_confirmation(True)
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.oDlg.vbox.pack_start(self.oFileChooser)
        self.oDlg.connect("response", self.handle_response)
        self.oDlg.show_all()
        self.oDlg.run()
        self.oDlg.destroy()

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by the function signature
    def handle_response(self, oWidget, oResponse):
        """Handle the users response. Write the text output to file."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        if oResponse ==  gtk.RESPONSE_OK:
            sFileName = self.oFileChooser.get_filename()
            if sFileName is not None:
                if self.view.cSetType == PhysicalCardSet:
                    oCardSet = PhysicalCardSet.byName(self.view.sSetName)
                elif self.view.cSetType == AbstractCardSet:
                    oCardSet = AbstractCardSet.byName(self.view.sSetName)
                else:
                    return
                sAuthor = oCardSet.author
                sComment = oCardSet.comment
                oWriter = WriteArdbText()
                fOut = file(sFileName,"w")
                oWriter.write(fOut, self.view.sSetName, sAuthor, sComment,
                        self.get_cards())
                fOut.close()
    # pylint: enable-msg=W0613

    def get_cards(self):
        """Get the cards from the card set."""
        # pylint: disable-msg=E1101
        # SQLObject methods confuse pylint
        dDict = {}
        for oCard in self.model.get_card_iterator(None):
            oACard = IAbstractCard(oCard)
            dDict.setdefault((oACard.id, oACard.name), 0)
            dDict[(oACard.id, oACard.name)] += 1
        return dDict

# pylint: disable-msg=C0103
# accept plugin name
plugin = CardSetExportArdbText
