# Rulebook.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Downloads a rulebook HTML page and makes it available via the Help menu."""

import gtk
import os
import re
import webbrowser
import urllib
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ProgressDialog import ProgressDialog
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists
from sutekh.io.WwFile import WwFile

# pylint: disable-msg=R0904
# R0904 - gtk Widget, so has many public methods
class RulebookConfigDialog(SutekhDialog):
    """Dialog for configuring the Rulebook plugin."""

    WW_RULEBOOK_URL = "http://www.white-wolf.com/vtes/rulebook/rulebook.html"

    def __init__(self, oParent, bFirstTime=False):
        super(RulebookConfigDialog, self).__init__('Configure Rulebook Plugin',
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))

        oDescLabel = gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook '
                    'plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook '
                    'plugin</b>\nChoose cancel to skip configuring the '
                    'plugin\nYou will not be prompted again')

        self.oSourceWw = gtk.RadioButton(
                label='Download from www.white-wolf.com')

        self.oSourceUrl = gtk.RadioButton(self.oSourceWw,
                label='Download from other URL')
        self.oUrlEntry = gtk.Entry()

        self.oSourceFile = gtk.RadioButton(self.oSourceWw,
                label='Select local file')
        self.oFileChooser = gtk.FileChooserWidget(
                action=gtk.FILE_CHOOSER_ACTION_OPEN)
        oHtmlFilter = gtk.FileFilter()
        oHtmlFilter.add_pattern('*.html')
        oHtmlFilter.add_pattern('*.HTML')
        self.oFileChooser.add_filter(oHtmlFilter)

        # box for holding additional widgets for the various source
        # options
        oSubBox = gtk.VBox(False, 2)

        self.oSourceWw.connect('toggled', self._radio_toggled, oSubBox, None)
        self.oSourceUrl.connect('toggled', self._radio_toggled, oSubBox,
                self.oUrlEntry)
        self.oSourceFile.connect('toggled', self._radio_toggled, oSubBox,
                self.oFileChooser)

        self.oSourceWw.set_active(True)

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self.oSourceWw, False, False)
        self.vbox.pack_start(self.oSourceUrl, False, False)
        self.vbox.pack_start(self.oSourceFile, False, False)
        self.vbox.pack_start(oSubBox)
        self.set_size_request(600, 600)

        self.show_all()

    def _radio_toggled(self, oRadioButton, oSubBox, oNewChild):
        """Display the correct sub-widgets when radio buttons change"""
        if oRadioButton.get_active():
            for oChild in oSubBox.get_children():
                oSubBox.remove(oChild)
            if oNewChild:
                oSubBox.pack_start(oNewChild)
            self.show_all()

    def get_url(self):
        """Get the url selected for download (or None)."""
        if self.oSourceWw.get_active():
            return self.WW_RULEBOOK_URL
        elif self.oSourceUrl.get_active():
            return self.oUrlEntry.get_text()
        else:
            return None

    def get_file(self):
        """Get the file name selected (or None)."""
        if self.oSourceFile.get_active():
            return self.oFileChooser.get_filename()
        else:
            return None


class RulebookPlugin(CardListPlugin):
    """Plugin allowing downloading of a rulebook and making it available
       via the Help menu.
       """
    aModelsSupported = ["MainWindow"]

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(RulebookPlugin, self).__init__(*aArgs, **kwargs)
        self._oRulebookDlg = None
        self._sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'rulebook')
        self._oConfigMenuItem = None
        self._oHelpMenuItem = None

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the images can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None

        self._oConfigMenuItem = gtk.MenuItem("Configure Rulebook Plugin")
        self._oConfigMenuItem.connect("activate", self.config_activate)

        self._oHelpMenuItem = gtk.MenuItem("Rulebook")
        self._oHelpMenuItem.connect("activate", self.rulebook_activate)

        if not os.path.isfile(os.path.join(self._sPrefsPath, "rulebook.html")):
            self._oHelpMenuItem.set_sensitive(False)

        return [('Plugins', self._oConfigMenuItem),
                ('Plugins', self._oHelpMenuItem)]

    def setup(self):
        """Prompt the user to download/setup the rulebook the first time"""
        if not os.path.exists(self._sPrefsPath):
            # Looks like the first time
            oDialog = RulebookConfigDialog(self.parent, True)
            self.handle_config_response(oDialog)
            # Don't get called next time
            ensure_dir_exists(self._sPrefsPath)

    # pylint: disable-msg=W0613
    # oMenuWidget needed by gtk function signature
    def config_activate(self, oMenuWidget):
        """Launch the configuration dialog."""
        oDialog = RulebookConfigDialog(self.parent, False)
        self.handle_config_response(oDialog)

    # pylint: disable-msg=W0613
    # oMenuWidget needed by gtk function signature
    def rulebook_activate(self, oMenuWidget):
        """Show the rulebook."""
        sPath = os.path.join(self._sPrefsPath, "rulebook.html")
        sPath = os.path.abspath(sPath)
        sDrive, sPath = os.path.splitdrive(sPath)
        if sDrive:
            sPath = sDrive + "|" + sPath
        sPath = sPath.replace(os.path.sep, "/")
        if not sPath.startswith("/"):
            sPath = "/" + sPath
        sUrl = "file:///" + sPath
        webbrowser.open(sUrl)

    def _link_resource(self, sLocalUrl):
        """Return a file-like object which sLocalUrl can be read from."""
        sResource = os.path.join(self._sPrefsPath, sLocalUrl)
        if os.path.exists(sResource):
            return file(sResource, 'rb')
        else:
            raise ValueError("Unknown resource %s" % sLocalUrl)

    def handle_config_response(self, oConfigDialog):
        """Handle the response from the config dialog"""
        iResponse = oConfigDialog.run()
        bActivateMenu = False

        if iResponse == gtk.RESPONSE_OK:
            sUrl = oConfigDialog.get_url()
            sFile = oConfigDialog.get_file()

            if sUrl is not None:
                if self._download_rulebook(sUrl):
                    bActivateMenu = True
                else:
                    do_complaint_error('Unable to successfully download '
                                        'rulebook from %s' % (sUrl,))
            elif sFile is not None:
                if self._copy_rulebook(sFile):
                    bActivateMenu = True
                else:
                    do_complaint_error('Unable to successfully copy '
                                        'rulebook from %s' % (sFile,))
            else:
                # something weird happened
                pass

        if bActivateMenu:
            # Update the menu display if needed
            self._oHelpMenuItem.set_sensitive(True)

        # get rid of the dialog
        oConfigDialog.destroy()

    def _download_rulebook(self, sUrl):
        """Download a rulebook from a URL."""
        try:
            oFile = WwFile(sUrl, bUrl=True).open()
            sLength = oFile.info().getheader('Content-Length')
            if sLength:
                sData = ""
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
                        sData += sInf
                    else:
                        bCont = False
                        oProgress.destroy()
            else:
                # Just try and download
                sData = oFile.read()

            return self._save_rulebook(sData)
        # pylint: disable-msg=W0703
        # We really do want to catch all exceptions here
        except Exception:
            return False

    def _copy_rulebook(self, sFile):
        """Copy the rulebook from a local file."""
        try:
            oFile = WwFile(sFile).open()
            sData = oFile.read()
            return self._save_rulebook(sData)
        # pylint: disable-msg=W0703
        # We really do want to catch all exceptions here
        except Exception:
            return False

    def _save_rulebook(self, sData):
        """Save the data from a rulebook to the preferences folder."""
        sData = self._clean_rulebook(sData)

        ensure_dir_exists(self._sPrefsPath)
        sFile = os.path.join(self._sPrefsPath, "rulebook.html")

        oFile = file(sFile, 'wb')
        oFile.write(sData)
        oFile.close()

        if os.path.isfile(sFile):
            return True
        return False

    @staticmethod
    def _clean_rulebook(sData):
        """Clean up rulebook HTML"""
        # img tags are always short tags in the WW rulebook file
        oShortTags = set(['hr', 'br', 'img'])

        oStartTagRe = re.compile(r"<\s*(?P<name>[A-Z0-9a-z_]+)"
            r"(?P<attrs>[^>]*)>",
            re.MULTILINE)
        oEndTagRe = re.compile(r"</\s*(?P<name>[A-Z0-9a-z_]+)\s*>",
            re.MULTILINE)
        oAttrRe = re.compile(r"(?P<attr>\w+)\s*=\s*" \
                             r"(?P<value>\"(?:[^\"]|\\\")*\"|'[^']*'|[^\s]*)",
            re.MULTILINE)

        def fix_attr(oMatch):
            """Fix attribute."""
            sName = oMatch.group('attr').lower()
            sValue = oMatch.group('value')
            if sValue.startswith("'") or sValue.endswith("'"):
                sValue = "'%s'" % (sValue.strip("'"),)
            else:
                sValue = "\"%s\"" % (sValue.strip("\""),)
            return "%s=%s" % (sName, sValue)

        def fix_start_tag(oMatch):
            """Standardize start tags."""
            sName = oMatch.group('name').lower()
            sAttrs = oMatch.group('attrs')
            sAttrs = oAttrRe.sub(fix_attr, sAttrs)
            if sName in oShortTags and not sAttrs.endswith("/"):
                return "<%s%s/>" % (sName, sAttrs)
            else:
                return "<%s%s>" % (sName, sAttrs)

        def fix_end_tag(oMatch):
            """Standardize end tags."""
            sName = oMatch.group('name').lower()
            return "</%s>" % (sName,)

        sData = oStartTagRe.sub(fix_start_tag, sData)
        sData = oEndTagRe.sub(fix_end_tag, sData)

        # remove <img> and <script> tags since they're not
        # vital to the rulebook and avoid attempts by the
        # browser to access the network
        oImgTag = re.compile(r"<(img|script)[^<>]*>",
            re.MULTILINE)
        sData = oImgTag.sub("", sData)

        # unclosed <a name=...>
        oUnclosedName = re.compile(r"(<a name=[^>]*>[^<>]*"
            r"<h.>[^<>]*</h.>[^<>]*)<p>",
            re.MULTILINE)

        sData = oUnclosedName.sub(r"\g<1></a><p>", sData)

        # base url for href's that begin with . or /
        sBaseUrl = RulebookConfigDialog.WW_RULEBOOK_URL.rsplit("/", 1)[0]
        oHref = re.compile(r"(?P<start>href=[\"'])(?P<href>[^\"']*)"
                            r"(?P<end>[\"'])")

        def apply_base_url(oMatch):
            """Apply a base url to hrefs that start with . or /"""
            sHref = oMatch.group("href")
            if sHref.startswith(".") or sHref.startswith("/"):
                sHref = urllib.basejoin(sBaseUrl, sHref)
            return oMatch.group("start") + sHref + oMatch.group("end")

        sData = oHref.sub(apply_base_url, sData)

        return sData

# pylint: disable-msg=C0103
# shut up complaint about the name
plugin = RulebookPlugin
