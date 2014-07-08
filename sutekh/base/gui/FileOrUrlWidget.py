# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for loading a file either from a URL or a local file."""

import gtk
import os.path
from ..io.EncodedFile import EncodedFile
from ..io.UrlOps import urlopen_with_timeout
from .SutekhFileWidget import SutekhFileButton
from .GuiDataPack import gui_error_handler, progress_fetch_data


class FileOrUrlWidget(gtk.VBox):
    """Compound widget for loading a file from either a URL or a local file."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods

    OTHER_FILE = 'Select file ...'
    OTHER_URL = 'Enter other URL ...'

    # pylint: disable-msg=R0913, C0103
    # R0913: Need this many arguments
    # C0103: Use gtk naming conventions here for consistency when called
    def __init__(self, oParent, sTitle=None, dUrls=None,
                homogeneous=False, spacing=0):
        """Create a FileOrUrlWidget.

           dUrls is used a dictionary of URLs to suggest to the user.
           dUrls' keys are URL names, its values are URLs.
           'Enter other URL ...' and 'Select file ...' may not be used as
           a key in dUrls.
           """
        super(FileOrUrlWidget, self).__init__(homogeneous=homogeneous,
                spacing=spacing)
        if dUrls is None:
            dUrls = {}
        self._dUrls = dUrls
        if sTitle is None:
            sTitle = 'Select file ...'
        self._sTitle = sTitle

        assert(self.OTHER_URL not in self._dUrls)

        # setup src selector

        self._oSrcCombo = gtk.combo_box_new_text()
        for sName in sorted(self._dUrls):
            self._oSrcCombo.append_text(sName)

        self._oSrcCombo.append_text(self.OTHER_FILE)
        self._oSrcCombo.append_text(self.OTHER_URL)
        self._oSrcCombo.connect('changed', self._src_combo_updated)

        self._oSubBox = gtk.VBox(homogeneous=homogeneous, spacing=spacing)

        self._oUrlLabel = gtk.Label()  # for displaying suggested URLs
        self._oUrlLabel.set_justify(gtk.JUSTIFY_LEFT)
        self._oUrlLabel.set_line_wrap(True)
        self._oUrlLabel.set_alignment(0.0, 0.5)
        self._oUrlLabel.set_padding(10, 10)
        self._oUrlLabel.set_selectable(True)

        self._oUrlEntry = gtk.Entry()  # for entering custom URLs
        self._oFileButton = SutekhFileButton(oParent, sTitle)

        # pack

        if self._sTitle:
            oLabel = gtk.Label()
            oLabel.set_justify(gtk.JUSTIFY_LEFT)
            oLabel.set_markup('<b>%s</b>' % (sTitle,))
            oLabel.set_alignment(0.0, 0.5)
            self.pack_start(oLabel)
        self.pack_start(self._oSrcCombo)
        self.pack_start(self._oSubBox)

        self._oSrcCombo.set_active(0)
        self._src_combo_updated(self._oSrcCombo)

    # pylint: enable-msg=R0913, C0103

    def _src_combo_updated(self, oSrcCombo):
        """Handle updating of the selected source combo box."""
        sName = oSrcCombo.get_active_text()

        for oChild in self._oSubBox.get_children():
            self._oSubBox.remove(oChild)

        if sName == self.OTHER_URL:
            self._oSubBox.pack_start(self._oUrlEntry)
        elif sName == self.OTHER_FILE:
            self._oSubBox.pack_start(self._oFileButton)
        elif sName in self._dUrls:
            self._oUrlLabel.set_text(self._dUrls[sName])
            self._oSubBox.pack_start(self._oUrlLabel)
        else:
            # something weird happened
            pass

        self._oSubBox.show_all()

    def select_by_name(self, sToSelect):
        """Select the given entry by text.

           return True on success, False otherwise (value isn't in the list)"""
        oListModel = self._oSrcCombo.get_model()
        oIter = oListModel.get_iter_first()
        iPos = 0
        while oIter:
            sValue = oListModel.get_value(oIter, 0)
            if sValue == sToSelect:
                self._oSrcCombo.set_active(iPos)
                return True
            iPos += 1
            oIter = oListModel.iter_next(oIter)
        return False

    def get_file_or_url(self):
        """Return the selected file name or URL and whether the result
           represents a URL.

           E.g.  ("http://www.example.com/myfile.html", True)
                 ("/home/user/myfile.html", False)
           """
        sName = self._oSrcCombo.get_active_text()
        if sName == self.OTHER_URL:
            return self._oUrlEntry.get_text(), True
        elif sName == self.OTHER_FILE:
            return self._oFileButton.get_filename(), False
        elif sName in self._dUrls:
            return self._dUrls[sName], True
        else:
            # something weird happened
            return None, False

    def get_wwfile_data(self):
        """Open the selected file as a EncodedFile and retrieve the data.

           Will attempt to display a progress dialog if the file is a URL.
           """
        sUrl, bUrl = self.get_file_or_url()

        oFile = EncodedFile(sUrl, bUrl=bUrl).open()

        return progress_fetch_data(oFile)

    def get_binary_data(self, oOutFile=None):
        """Open the selected file and retrieve the binary data.

           Will attempt to display a progress dialog if the file is a URL.
           """
        sUrl, bUrl = self.get_file_or_url()

        if bUrl:
            oFile = urlopen_with_timeout(sUrl, fErrorHandler=gui_error_handler)
        else:
            oFile = file(sUrl, "rb")

        if not oFile:
            # Probable timeout in urlopen, so bail
            return None

        return progress_fetch_data(oFile, oOutFile)

    # Methods needed by the add_filter utility function in SutekhFileWidget

    def add_filter(self, oFilter):
        """Add a filter to the file button"""
        self._oFileButton.add_filter(oFilter)

    def set_filter(self, oFilter):
        """Set the active filter on the file button"""
        self._oFileButton.set_filter(oFilter)


class FileOrDirOrUrlWidget(FileOrUrlWidget):
    """Allow the user to select either a file, an url or a directory"""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods

    OTHER_DIR = 'Select directory ...'

    # pylint: disable-msg=R0913, C0103
    # R0913: Need this many arguments
    # C0103: Use gtk naming conventions here for consistency when called
    def __init__(self, oParent, sTitle=None, sDirTitle=None,
            sDefaultDir=None, dUrls=None, homogeneous=False, spacing=0):
        """Create a FileOrDirOrUrlWidget.
           """
        super(FileOrDirOrUrlWidget, self).__init__(oParent, sTitle, dUrls,
                homogeneous=homogeneous, spacing=spacing)

        if not sDirTitle:
            sDirTitle = 'Select directory ...'
        self._oDirButton = SutekhFileButton(oParent, sDirTitle)
        self._oDirButton.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        if sDefaultDir and os.path.exists(sDefaultDir) and \
                os.path.isdir(sDefaultDir):
            # File widget doesn't like being pointed at non-dirs
            # when in SELECT_FOLDER mode
            self._oDirButton.set_current_folder(sDefaultDir)

        self._oSrcCombo.append_text(self.OTHER_DIR)

    # pylint: enable-msg=R0913, C0103

    def _src_combo_updated(self, oSrcCombo):
        """Handle updating of the selected source combo box."""
        sName = oSrcCombo.get_active_text()

        super(FileOrDirOrUrlWidget, self)._src_combo_updated(oSrcCombo)

        # Only need to consider this case
        if sName == self.OTHER_DIR:
            self._oSubBox.pack_start(self._oDirButton)
            self._oSubBox.show_all()

    def get_file_or_dir_or_url(self):
        """Return the selected file name, directory or URL and
           whether the result represents a URL and whether a directory

           E.g.  ("http://www.example.com/myfile.html", True, False)
                 ("/home/user/myfile.html", False, False)
                 ("/home/user/cache/", False, True)
           The two flags is a bit messy, but keeps similiarties with parent
           class
           """
        sFile, bUrl = self.get_file_or_url()
        if sFile:
            # Not the directory case
            return sFile, bUrl, False
        # Need to check for the directory case
        sName = self._oSrcCombo.get_active_text()
        if sName == self.OTHER_DIR:
            return self._oDirButton.get_filename(), False, True
        else:
            return None, False, False
