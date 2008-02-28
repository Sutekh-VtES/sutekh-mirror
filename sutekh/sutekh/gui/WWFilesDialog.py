# WWFilesDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for handling loading of WW cardlist and rulings
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.io.WwFile import WW_CARDLIST_URL, WW_RULINGS_URL

class WWFilesDialog(SutekhDialog):
    def __init__(self, oParent):
        super(WWFilesDialog, self).__init__("Choose White Wolf Files", oParent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
            gtk.RESPONSE_CANCEL))
        oCardListLabel = gtk.Label("White Wolf CardList File:")
        self.oCardListFileButton = gtk.FileChooserButton("White Wolf cardlist")
        self.oUseWwCardListButton = gtk.CheckButton(label="Grab cardlist from White Wolf website?")

        oRulingsLabel = gtk.Label("White Wolf Rulings File (optional):")
        self.oRulingsFileButton = gtk.FileChooserButton("White Wolf rulings file")
        self.oUseWwRulingsButton = gtk.CheckButton(label="Grab rulings from White Wolf website?")

        self.oBackupFileButton = gtk.CheckButton(label="Backup database contents to File?")
        self.oBackupFileButton.set_active(False)
        self.oBackupFileLabel = gtk.Label("(None)")
        self.oBackupFileDialog = gtk.FileChooserDialog("Database Backup file",
                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.oBackupFileDialog.set_do_overwrite_confirmation(True)

        self.vbox.pack_start(oCardListLabel)
        self.vbox.pack_start(self.oCardListFileButton)
        self.vbox.pack_start(self.oUseWwCardListButton)
        self.vbox.pack_start(oRulingsLabel)
        self.vbox.pack_start(self.oRulingsFileButton)
        self.vbox.pack_start(self.oUseWwRulingsButton)
        self.vbox.pack_start(self.oBackupFileButton)
        self.vbox.pack_start(self.oBackupFileLabel)

        self.oBackupFileButton.connect("toggled", self.handleCheckButton)
        self.oUseWwCardListButton.connect("toggled", self.handleUseWwCardListToggle)
        self.oUseWwRulingsButton.connect("toggled", self.handleUseWwRulingsToggle)
        self.connect("response", self.handleResponse)

        self.show_all()
        self.sCLName = None
        self.sRulingsName = None
        self.sBackupFileName = None
        self.bCLIsUrl = None
        self.bRulingsIsUrl = None

    def handleResponse(self, oWidget, iResponse):
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

    def getNames(self):
        return (self.sCLName, self.bCLIsUrl, self.sRulingsName, self.bRulingsIsUrl, self.sBackupFileName)

    def handleCheckButton(self, oWidget):
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

    def handleUseWwCardListToggle(self, oWidget):
        if self.oUseWwCardListButton.get_active():
            self.oCardListFileButton.hide()
        else:
            self.oCardListFileButton.show()

    def handleUseWwRulingsToggle(self, oWidget):
        if self.oUseWwRulingsButton.get_active():
            self.oRulingsFileButton.hide()
        else:
            self.oRulingsFileButton.show()
