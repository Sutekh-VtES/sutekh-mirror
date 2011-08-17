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
from sutekh.io.WwFile import WW_CARDLIST_URL, WW_RULINGS_URL, EXTRA_CARD_URL


def make_alignment(oLabel, oFileButton, oUseButton):
    """Helper function for constructing the import dialog"""
    oAlign = gtk.Alignment(yalign=0.5, xscale=1.0)
    oAlign.set_padding(0, 15, 0, 0)
    oVBox = gtk.VBox(False, 2)
    oVBox.pack_start(oLabel)
    oVBox.pack_start(oFileButton)
    oVBox.pack_start(oUseButton)
    oAlign.add(oVBox)
    return oAlign


class WWFilesDialog(SutekhDialog):
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we keep a lot of internal state, so many instance variables
    """Actual dialog widget"""

    def __init__(self, oParent, bDisableBackup):
        super(WWFilesDialog, self).__init__("Choose White Wolf Files", oParent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL))
        oCardListLabel = gtk.Label()
        oCardListLabel.set_markup("<b>Official Card List:</b>")
        self._oParent = oParent
        self.oCardListFileButton = SutekhFileButton(oParent,
                "Official Card List")
        self.oCardListFileButton.add_filter_with_pattern('TXT files',
                ['*.txt'])
        self.oUseWwCardListButton = gtk.CheckButton(
                label="Grab official card list from V:EKN website?")

        oExtraLabel = gtk.Label()
        oExtraLabel.set_markup("<b>Additional Card List (optional):</b>")
        self.oExtraFileButton = SutekhFileButton(oParent,
                "Additional Card List")
        self.oExtraFileButton.add_filter_with_pattern('TXT files',
                ['*.txt'])
        self.oUseExtraUrlButton = gtk.CheckButton(
                label="Grab default additional cards (from bitbucket.org)?")

        oRulingsLabel = gtk.Label()
        oRulingsLabel.set_markup("<b>Official Rulings File (optional):</b>")
        self.oRulingsFileButton = SutekhFileButton(oParent,
                "Official Rulings File")
        self.oRulingsFileButton.add_filter_with_pattern('HTML files',
                ['*.html', '*htm'])
        self.oUseWwRulingsButton = gtk.CheckButton(
                label="Grab official rulings from V:EKN website?")

        self.oBackupFileButton = gtk.CheckButton(
                label="Backup database contents to File?")
        self.oBackupFileButton.set_active(False)
        self.oBackupFileLabel = gtk.Label("(None)")
        if bDisableBackup:
            self.oBackupFileButton.set_sensitive(False)
            self.oBackupFileLabel.set_sensitive(False)  # For consistency
        # We can't use SimpleFileDialog, as we need to hide + reshow
        self.oBackupFileDialog = SutekhFileDialog(oParent,
                "Database Backup file", gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oBackupFileDialog.set_do_overwrite_confirmation(True)

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oCardAlign = make_alignment(oCardListLabel,
                self.oCardListFileButton, self.oUseWwCardListButton)
        self.vbox.pack_start(oCardAlign)
        oExtraAlign = make_alignment(oExtraLabel, self.oExtraFileButton,
                self.oUseExtraUrlButton)
        self.vbox.pack_start(oExtraAlign)
        oRulingsAlign = make_alignment(oRulingsLabel, self.oRulingsFileButton,
                self.oUseWwRulingsButton)
        self.vbox.pack_start(oRulingsAlign)
        self.vbox.pack_start(self.oBackupFileButton)
        self.vbox.pack_start(self.oBackupFileLabel)

        self.oBackupFileButton.connect("toggled", self.backup_file_toggled)
        self.oUseWwCardListButton.connect("toggled",
                self.use_ww_cardlist_toggled)
        self.oUseExtraUrlButton.connect("toggled",
                self.use_extra_url_toggled)
        self.oUseWwRulingsButton.connect("toggled",
                self.use_ww_rulings_toggled)
        self.connect("response", self.handle_response)

        self.oUseWwCardListButton.set_active(True)
        self.oUseExtraUrlButton.set_active(True)
        self.oUseWwRulingsButton.set_active(True)

        self.show_all()
        self.sCLName = None
        self.sRulingsName = None
        self.sBackupFileName = None
        self.bCLIsUrl = None
        self.bRulingsIsUrl = None
        self.bExtraIsUrl = None
        self.sExtraName = None

    def handle_response(self, _oWidget, iResponse):
        """Extract the information from the dialog if the user presses OK"""
        if iResponse == gtk.RESPONSE_OK:
            if self.oUseWwCardListButton.get_active():
                self.bCLIsUrl = True
                self.sCLName = WW_CARDLIST_URL
            else:
                self.bCLIsUrl = False
                self.sCLName = self.oCardListFileButton.get_filename()

            if self.oUseExtraUrlButton.get_active():
                self.bExtraIsUrl = True
                self.sExtraName = EXTRA_CARD_URL
            else:
                self.bExtraIsUrl = False
                self.sExtraName = self.oExtraFileButton.get_filename()

            if self.oUseWwRulingsButton.get_active():
                self.bRulingsIsUrl = True
                self.sRulingsName = WW_RULINGS_URL
            else:
                self.bRulingsIsUrl = False
                self.sRulingsName = self.oRulingsFileButton.get_filename()

            if self.oBackupFileButton.get_active():
                self.sBackupFileName = self.oBackupFileDialog.get_filename()

    def get_names(self):
        """Pass the information back to the caller"""
        return (self.sCLName, self.bCLIsUrl, self.sExtraName, self.bExtraIsUrl,
                self.sRulingsName, self.bRulingsIsUrl, self.sBackupFileName)

    def backup_file_toggled(self, _oWidget):
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

    def use_ww_cardlist_toggled(self, _oWidget):
        """Update state if user toggles the 'Use WW cardlist' checkbox"""
        if self.oUseWwCardListButton.get_active():
            self.oCardListFileButton.set_sensitive(False)
        else:
            self.oCardListFileButton.set_sensitive(True)

    def use_ww_rulings_toggled(self, _oWidget):
        """Update state if the user toggles the 'Use WW rulings' checkbox"""
        if self.oUseWwRulingsButton.get_active():
            self.oRulingsFileButton.set_sensitive(False)
        else:
            self.oRulingsFileButton.set_sensitive(True)

    def use_extra_url_toggled(self, _oWidget):
        """Update state if the user toggles the 'Use WW rulings' checkbox"""
        if self.oUseExtraUrlButton.get_active():
            self.oExtraFileButton.set_sensitive(False)
        else:
            self.oExtraFileButton.set_sensitive(True)
