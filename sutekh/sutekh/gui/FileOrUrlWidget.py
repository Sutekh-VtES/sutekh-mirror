# FileOrUrlWidget.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for loading a file either from a URL or a local file."""

import gtk
import urllib2
from sutekh.gui.SutekhFileWidget import SutekhFileButton
from sutekh.io.WwFile import WwFile
from sutekh.gui.ProgressDialog import ProgressDialog

class FileOrUrlWidget(gtk.VBox):
    """Compound widget for loading a file from either a URL or a local file."""

    OTHER_FILE = 'Select file ...'
    OTHER_URL = 'Enter other URL ...'

    def __init__(self, oParent, sTitle=None, dUrls=None,
                homogeneous=False, spacing=0):
        """Create a FileOrUrlWidget.

           dUrls is used a dictionary of URLs to suggest to the user.
           dUrls' keys are URL names, its values are URLs. 'Enter other URL ...' and
           'Select file ...' may not be used as a key in dUrls.
           """
        super(FileOrUrlWidget, self).__init__(homogeneous=homogeneous, spacing=spacing)
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

        self._oUrlLabel = gtk.Label() # for displaying suggested URLs
        self._oUrlLabel.set_justify(gtk.JUSTIFY_LEFT)
        self._oUrlLabel.set_line_wrap(True)
        self._oUrlLabel.set_alignment(0.0, 0.5)
        self._oUrlLabel.set_padding(10, 10)
        self._oUrlLabel.set_selectable(True)

        self._oUrlEntry = gtk.Entry() # for entering custom URLs
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

    def get_file_or_url(self):
        """Return the selected file name or URL and whether the result represents a URL.

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
        """Open the selected file as a WwFile and retrieve the data.

           Will attempt to display a progress dialog if the file is a URL.
           """
        sUrl, bUrl = self.get_file_or_url()

        oFile = WwFile(sUrl, bUrl=bUrl).open()
        if hasattr(oFile, 'info') and callable(oFile.info):
            sLength = oFile.info().getheader('Content-Length')
        else:
            sLength = None

        if sLength:
            aData = []
            iLength = int(sLength)
            oProgress = ProgressDialog()
            oProgress.set_description('Download progress')
            iTotal = 0
            bCont = True
            while bCont:
                sInf = oFile.read(10000)
                iTotal += 10000
                oProgress.update_bar(float(iTotal) / iLength)
                if sInf:
                    aData.append(sInf)
                else:
                    bCont = False
                    oProgress.destroy()
            sData = ''.join(aData)
        else:
            # Just try and download
            sData = oFile.read()

        return sData

    def get_binary_data(self):
        """Open the selected file and retrieve the binary data.

           Will attempt to display a progress dialog if the file is a URL.
           """
        sUrl, bUrl = self.get_file_or_url()

        if bUrl:
            oFile = urllib2.urlopen(sUrl)
        else:
            oFile = file(sUrl, "rb")

        if hasattr(oFile, 'info') and callable(oFile.info):
            sLength = oFile.info().getheader('Content-Length')
        else:
            sLength = None

        if sLength:
            aData = []
            iLength = int(sLength)
            oProgress = ProgressDialog()
            oProgress.set_description('Download progress')
            iTotal = 0
            bCont = True
            while bCont:
                sInf = oFile.read(10000)
                iTotal += 10000
                oProgress.update_bar(float(iTotal) / iLength)
                if sInf:
                    aData.append(sInf)
                else:
                    bCont = False
                    oProgress.destroy()
            sData = ''.join(aData)
        else:
            # Just try and download
            sData = oFile.read()

        return sData
