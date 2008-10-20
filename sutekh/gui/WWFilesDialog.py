# WWFilesDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for handling loading of WW cardlist and rulings
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""File selection dialog for choosing cardlist and rulings files"""

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.SutekhFileWidget import SutekhFileDialog, SutekhFileButton
from sutekh.io.WwFile import WW_CARDLIST_URL, WW_RULINGS_URL

class WWFilesDialog(SutekhDialog):
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we keep a lot of internal state, so many instance variables
    """Actual dailog widget"""

    def __init__(self, oParent):
        super(WWFilesDialog, self).__init__("Choose White Wolf Files", oParent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL))
        oCardListLabel = gtk.Label("White Wolf Card List File:")
        self._oParent = oParent
        self.oCardListFileButton = SutekhFileButton(oParent,
                "White Wolf Card List")
        self.oCardListFileButton.add_filter_with_pattern('HTML files',
                ['*.html', '*htm'])
        self.oUseWwCardListButton = gtk.CheckButton(label=
                "Grab cardlist from White Wolf website?")

        oRulingsLabel = gtk.Label("White Wolf Rulings File (optional):")
        self.oRulingsFileButton = SutekhFileButton(oParent,
                "White Wolf rulings file")
        self.oRulingsFileButton.add_filter_with_pattern('HTML files',
                ['*.html', '*htm'])
        self.oUseWwRulingsButton = gtk.CheckButton(label=
                "Grab rulings from White Wolf website?")

        self.oBackupFileButton = gtk.CheckButton(label=
                "Backup database contents to File?")
        self.oBackupFileButton.set_active(False)
        self.oBackupFileLabel = gtk.Label("(None)")
        # We can't use SimpleFileDialog, as we need to hide + reshow
        self.oBackupFileDialog = SutekhFileDialog(oParent,
                "Database Backup file", gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oBackupFileDialog.set_do_overwrite_confirmation(True)

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.vbox.pack_start(oCardListLabel)
        self.vbox.pack_start(self.oCardListFileButton)
        self.vbox.pack_start(self.oUseWwCardListButton)
        self.vbox.pack_start(oRulingsLabel)
        self.vbox.pack_start(self.oRulingsFileButton)
        self.vbox.pack_start(self.oUseWwRulingsButton)
        self.vbox.pack_start(self.oBackupFileButton)
        self.vbox.pack_start(self.oBackupFileLabel)

        self.oBackupFileButton.connect("toggled", self.backup_file_toggled)
        self.oUseWwCardListButton.connect("toggled",
                self.use_ww_cardlist_toggled)
        self.oUseWwRulingsButton.connect("toggled",
                self.use_ww_rulings_toggled)
        self.connect("response", self.handle_response)

        self.show_all()
        self.sCLName = None
        self.sRulingsName = None
        self.sBackupFileName = None
        self.bCLIsUrl = None
        self.bRulingsIsUrl = None

    # pylint: disable-msg=W0613
    # oWidget required by the function signature
    def handle_response(self, oWidget, iResponse):
        """Extract the information from the dialog if the user presses OK"""
        if iResponse == gtk.RESPONSE_OK:
            if self.oUseWwCardListButton.get_active():
                self.bCLIsUrl = True
                self.sCLName = WW_CARDLIST_URL
            else:
                self.bCLIsUrl = False
                self.sCLName = self.oCardListFileButton.get_filename()

            if self.oUseWwRulingsButton.get_active():
                self.bRulingsIsUrl = True
                self.sRulingsName = WW_RULINGS_URL
            else:
                self.bRulingsIsUrl = False
                self.sRulingsName = self.oRulingsFileButton.get_filename()

            if self.oBackupFileButton.get_active():
                self.sBackupFileName = self.oBackupFileDialog.get_filename()

    # pylint: enable-msg=W0613

    def get_names(self):
        """Pass the information back to the caller"""
        return (self.sCLName, self.bCLIsUrl, self.sRulingsName,
                self.bRulingsIsUrl, self.sBackupFileName)

    # pylint: disable-msg=W0613
    # oWidget required by the function signature
    def backup_file_toggled(self, oWidget):
        """Update status if user toggles the 'make backup' checkbox"""
        if self.oBackupFileButton.get_active():
            self.oBackupFileDialog.run()
            self.oBackupFileDialog.hide()
            sTemp = self.oBackupFileDialog.get_filename()
            self.oBackupFileDialog.hide()
            if sTemp:
                self.oBackupFileLabel.set_text(sTemp)
            else:
                self.oBackupFileButton.set_active(False)
        else:
            self.oBackupFileLabel.set_text("(None)")

    def use_ww_cardlist_toggled(self, oWidget):
        """Update state if user toggles the 'Use WW cardlist' checkbox"""
        if self.oUseWwCardListButton.get_active():
            self.oCardListFileButton.hide()
        else:
            self.oCardListFileButton.show()

    def use_ww_rulings_toggled(self, oWidget):
        """Update state if the user toggles the 'Use WW rulings' checkbox"""
        if self.oUseWwRulingsButton.get_active():
            self.oRulingsFileButton.hide()
        else:
            self.oRulingsFileButton.show()
