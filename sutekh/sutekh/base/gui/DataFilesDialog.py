# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog for handling loading of cardlist, rulings and other such
# files
# Copyright 2014-2018 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""File selection dialog for choosing cardlist and rulings files"""

from collections import namedtuple
from urllib.parse import urlsplit

from gi.repository import Gtk
from .SutekhDialog import SutekhDialog
from .SutekhFileWidget import SutekhFileDialog, SutekhFileButton


WidgetHolder = namedtuple('WidgetHolder', ['oAlign', 'oFileWidget',
                                           'oUrlButton', 'sUrl'])

Result = namedtuple('Result', ['bIsUrl', 'sName'])

COMBINED_ZIP = 'Combined Zip File'


def make_alignment(oLabel, oFileButton, oUseButton=None):
    """Helper function for constructing the import dialog"""
    oAlign = Gtk.Alignment(yalign=0.5, xscale=1.0)
    oAlign.set_padding(0, 15, 0, 0)
    oVBox = Gtk.VBox(homogeneous=False, spacing=2)
    oVBox.pack_start(oLabel, True, True, 0)
    oVBox.pack_start(oFileButton, True, True, 0)
    if oUseButton:
        oVBox.pack_start(oUseButton, True, True, 0)
    oAlign.add(oVBox)
    return oAlign


def get_domain(sUrl):
    """Strip out the domain of the url"""
    sDomain = urlsplit(sUrl)[1]
    return sDomain


class DataFilesDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # we keep a lot of internal state, so many instance variables
    """Dialog that asks for the Data files or urls as required"""

    # pylint: disable=too-many-arguments
    # We need these arguments
    def __init__(self, oParent, tReaders, bDisplayZip, sZippedUrl,
                 bDisableBackup):
        # pylint: disable=too-many-locals, too-many-branches
        # pylint: disable=too-many-statements
        # Lots of stuff we need to setup to handle all the download options
        super().__init__(
            "Choose CardList Files", oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK, "_Cancel",
             Gtk.ResponseType.CANCEL))
        self.show()
        self._oParent = oParent
        self._dFileWidgets = {}
        self._dChoices = {}
        for oReader in tReaders:
            oFileLabel = Gtk.Label()
            if oReader.bRequired:
                oFileLabel.set_markup(
                    '<b>%s (required)</b>' % oReader.sDescription)
            else:
                oFileLabel.set_markup(
                    '<b>%s</b> (optional)' % oReader.sDescription)
            oFileButton = SutekhFileButton(oParent, oReader.sDescription)
            oFileButton.add_filter_with_pattern(*oReader.tPattern)
            if oReader.sUrl:
                oUrlButton = Gtk.CheckButton(
                    "Use default url (from %s)" % get_domain(oReader.sUrl))
                oFileAlign = make_alignment(oFileLabel, oFileButton,
                                            oUrlButton)
                # We assume that using the default file is the recommended
                # option, so we select it by default
                oUrlButton.set_active(True)
            else:
                oUrlButton = None
                oFileAlign = make_alignment(oFileLabel, oFileButton)
            self._dFileWidgets[oReader.sName] = WidgetHolder(oFileAlign,
                                                             oFileButton,
                                                             oUrlButton,
                                                             oReader.sUrl)
            self.vbox.pack_start(oFileAlign, True, True, 0)
            oFileAlign.show_all()

        self.oBackupFileButton = Gtk.CheckButton(
            label="Backup database contents to File?")
        self.oBackupFileButton.set_active(False)
        self.oBackupFileLabel = Gtk.Label(label="(None)")
        if bDisableBackup:
            self.oBackupFileButton.set_sensitive(False)
            self.oBackupFileLabel.set_sensitive(False)  # For consistency
        # We can't use SimpleFileDialog, as we need to hide + reshow
        self.oBackupFileDialog = SutekhFileDialog(
            oParent, "Database Backup file", Gtk.FileChooserAction.SAVE,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))
        self.oBackupFileDialog.set_do_overwrite_confirmation(True)

        self._oHideZip = None
        if bDisplayZip:
            # Hide the ordinary file widgets
            oZipLabel = Gtk.Label()
            oZipLabel.set_markup('<b>%s</b>' % COMBINED_ZIP)
            oZipButton = SutekhFileButton(oParent, COMBINED_ZIP)
            oZipButton.add_filter_with_pattern("ZIP files", ["*.zip"])
            if sZippedUrl:
                oZipUrlCheckBox = Gtk.CheckButton("Use default url (from %s)" %
                                                  get_domain(sZippedUrl))
                oZipAlign = make_alignment(oZipLabel, oZipButton,
                                           oZipUrlCheckBox)
                # We assume that using the default zip file is the recommended
                # option, so we select it by default
                oZipUrlCheckBox.set_active(True)
                # The logic around the show / hide individual files and zip
                # files ensures that the this doesn't clash with the indivual
                # file defaults.
            else:
                oZipUrlCheckBox = None
                oZipAlign = make_alignment(oZipLabel, oZipButton)
            self._dFileWidgets[COMBINED_ZIP] = WidgetHolder(oZipAlign,
                                                            oZipButton,
                                                            oZipUrlCheckBox,
                                                            sZippedUrl)
            self._oHideZip = Gtk.CheckButton("Show individual file buttons")
            self.vbox.pack_start(oZipAlign, True, True, 0)
            self.vbox.pack_start(self._oHideZip, True, True, 0)
            # We need to show_all, even if we later hide this, to display
            # all the buttons and such correctly.
            oZipAlign.show_all()
            if sZippedUrl:
                # Default to showing the zip option only
                for sName, oWidgets in self._dFileWidgets.items():
                    if sName != COMBINED_ZIP:
                        oWidgets.oAlign.hide()
                self._oHideZip.set_active(False)
            else:
                # Hide the zip file option
                self._oHideZip.set_active(True)
                oZipAlign.hide()
            self._oHideZip.connect("toggled", self.hide_zip_toggled)
            self._oHideZip.show()

        self.vbox.pack_start(self.oBackupFileButton, True, True, 0)
        self.vbox.pack_start(self.oBackupFileLabel, True, True, 0)
        self.oBackupFileLabel.show()
        self.oBackupFileButton.show()

        self.oBackupFileButton.connect("toggled", self.backup_file_toggled)
        self.connect("response", self.handle_response)

        self.sBackupFileName = None

    # pylint: enable=too-many-arguments

    def handle_response(self, _oWidget, iResponse):
        """Extract the information from the dialog if the user presses OK"""
        if iResponse == Gtk.ResponseType.OK:
            if self._oHideZip:
                bUseZip = not self._oHideZip.get_active()
            else:
                bUseZip = False
            self._dChoices = {}
            for sName, oWidgets in self._dFileWidgets.items():
                if bUseZip and sName != COMBINED_ZIP:
                    # Only take from the zip file entry
                    continue
                if not bUseZip and sName == COMBINED_ZIP:
                    # Skip the zip file settings
                    continue
                if oWidgets.oUrlButton and oWidgets.oUrlButton.get_active():
                    self._dChoices[sName] = Result(bIsUrl=True,
                                                   sName=oWidgets.sUrl)
                else:
                    self._dChoices[sName] = Result(
                        bIsUrl=False,
                        sName=oWidgets.oFileWidget.get_filename())
            if self.oBackupFileButton.get_active():
                self.sBackupFileName = self.oBackupFileDialog.get_filename()

    def get_names(self):
        """Pass the information back to the caller"""
        return self._dChoices, self.sBackupFileName

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

    def hide_zip_toggled(self, _oWidget):
        """Update status if user toggles the 'show individual files'
           checkbox"""
        bHideZip = self._oHideZip.get_active()
        for sName, oWidgets in self._dFileWidgets.items():
            oAlign = oWidgets.oAlign
            # pylint: disable=expression-not-assigned
            # We use the inline syntax for compactness and readablity
            if sName == COMBINED_ZIP:
                oAlign.hide() if bHideZip else oAlign.show()
            else:
                oAlign.show() if bHideZip else oAlign.hide()
