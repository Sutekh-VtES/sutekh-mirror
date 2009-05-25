# Rulebook.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Downloads rulebook HTML pages and makes them available via the Help menu."""

import gtk
import os
import re
import webbrowser
import urllib
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.ProgressDialog import ProgressDialog
from sutekh.gui.SutekhFileWidget import SutekhFileButton
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists
from sutekh.io.WwFile import WwFile

# pylint: disable-msg=R0904
# R0904 - gtk Widget, so has many public methods
class RulebookConfigDialog(SutekhDialog):
    """Dialog for configuring the Rulebook plugin."""

    POSSIBLE_FILES = [
            "Rulebook", "Imbued Rules", "Rulings", "V:EKN Tournament Rules",
            "VTES FAQ", "V:TES Complete Rules Reference",
    ]

    WW_RULEBOOK_URLS = {
        "Rulebook": "http://www.white-wolf.com/vtes/rulebook/rulebook.html",
        "Imbued Rules":
           "http://www.white-wolf.com/vtes/?line=Checklist_NightsOfReckoning",
        "Rulings": "http://www.white-wolf.com/vtes/index.php?line=rulings",
        "V:EKN Tournament Rules":
           "http://www.white-wolf.com/vtes/index.php?line=veknRules",
        "VTES FAQ": "http://www.thelasombra.com/vtes_faq.htm",
        "V:TES Complete Rules Reference":
           "http://www.white-wolf.com/vtes/?line=outline",
    }

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
                label='Download from www.white-wolf.com and'
                ' www.thelasombra.com')

        self.oSourceUrl = gtk.RadioButton(self.oSourceWw,
                label='Download from other URL(s)')

        # SourceUrl sub-components
        oUrlSub = gtk.VBox(False, 2)
        self.dUrlSubEntries = {}
        for sName in self.POSSIBLE_FILES:
            oLabel = gtk.Label(sName)
            oEntry = gtk.Entry()
            oHBox = gtk.HBox(False, 2)
            oHBox.pack_start(oLabel, expand=False, padding=2)
            oHBox.pack_start(oEntry)
            oUrlSub.pack_start(oHBox)
            self.dUrlSubEntries[sName] = oEntry

        self.oSourceFile = gtk.RadioButton(self.oSourceWw,
                label='Select local files')

        # SourceFile sub-components
        oFileSub = gtk.VBox(False, 2)
        self.dFileSubButtons = {}
        for sName in self.POSSIBLE_FILES:
            oLabel = gtk.Label(sName)
            oFileButton = SutekhFileButton(oParent,
                "Select %s HTML file" % (sName,))
            oFileButton.add_filter_with_pattern('HTML files',
                ['*.html', '*.htm'])
            oHBox = gtk.HBox(False, 2)
            oHBox.pack_start(oLabel, expand=False, padding=2)
            oHBox.pack_start(oFileButton)
            oFileSub.pack_start(oHBox)
            self.dFileSubButtons[sName] = oFileButton

        # box for holding additional widgets for the various source
        # options
        oSubBox = gtk.VBox(False, 2)

        self.oSourceWw.connect('toggled', self._radio_toggled, oSubBox, None)
        self.oSourceUrl.connect('toggled', self._radio_toggled, oSubBox,
            oUrlSub)
        self.oSourceFile.connect('toggled', self._radio_toggled, oSubBox,
            oFileSub)

        self.oSourceWw.set_active(True)

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        self.vbox.pack_start(self.oSourceWw, False, False)
        self.vbox.pack_start(self.oSourceUrl, False, False)
        self.vbox.pack_start(self.oSourceFile, False, False)
        self.vbox.pack_start(oSubBox)

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
            return dict(self.WW_RULEBOOK_URLS)
        elif self.oSourceUrl.get_active():
            return dict([(sName, self.dUrlSubEntries[sName].get_text())
                for sName in self.POSSIBLE_FILES])
        else:
            return None

    def get_file(self):
        """Get the file name selected (or None)."""
        if self.oSourceFile.get_active():
            return dict([(sName, self.dFileSubButtons[sName].get_filename())
                for sName in self.POSSIBLE_FILES])
        else:
            return None


class RulebookPlugin(CardListPlugin):
    """Plugin allowing downloading of rulebook HTML pages and making them
       available via the Plugins menu.
       """
    aModelsSupported = ["MainWindow"]

    POSSIBLE_FILES = RulebookConfigDialog.POSSIBLE_FILES
    WW_RULEBOOK_URLS = RulebookConfigDialog.WW_RULEBOOK_URLS

    LOCAL_NAMES = {
        "Rulebook": "rulebook.html",
        "Imbued Rules": "imbued.html",
        "Rulings": "rulings.html",
        "V:EKN Tournament Rules": "tournament_rules.html",
        "VTES FAQ" : "faq.html",
        "V:TES Complete Rules Reference": "rules_reference.html",
    }

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *aArgs, **kwargs):
        super(RulebookPlugin, self).__init__(*aArgs, **kwargs)
        self._oRulebookDlg = None
        self._dMenuItems = None
        self._sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'rulebook')

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the files can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None

        oSubMenu = gtk.Menu()
        oMenuItem = gtk.MenuItem("Rulebook")
        oMenuItem.set_submenu(oSubMenu)

        oConfigMenuItem = gtk.MenuItem("Configure Rulebook Plugin")
        oConfigMenuItem.connect("activate", self.config_activate)
        oSubMenu.add(oConfigMenuItem)

        self._dMenuItems = {}
        for sName in self.POSSIBLE_FILES:
            oItem = gtk.MenuItem(sName)
            oItem.connect("activate", self.rulebook_activate, sName)
            self._dMenuItems[sName] = oItem
            oSubMenu.add(oItem)

        self._update_menu()

        return [('Plugins', oMenuItem)]

    def _update_menu(self):
        """Check for existence of files and update which menu items are active
           accordingly.
           """
        for sName, sFile in self.LOCAL_NAMES.items():
            if not os.path.isfile(os.path.join(self._sPrefsPath, sFile)):
                self._dMenuItems[sName].set_sensitive(False)
            else:
                self._dMenuItems[sName].set_sensitive(True)

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
    def rulebook_activate(self, oMenuWidget, sName):
        """Show HTML file associated with the sName."""
        sPath = os.path.join(self._sPrefsPath, self.LOCAL_NAMES[sName])
        sPath = os.path.abspath(sPath)
        sDrive, sPath = os.path.splitdrive(sPath)
        # os.path.splitdrive assumes that drives have the form "X:"
        # so do the same in our replace.
        sPath = sDrive.replace(":", "|") + sPath
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

        if iResponse == gtk.RESPONSE_OK:
            dUrls = oConfigDialog.get_url()
            dFiles = oConfigDialog.get_file()

            if dUrls is not None:
                if not self._download_files(dUrls):
                    do_complaint_error('Unable to successfully download '
                                        'some or all of the rulebook files')
            elif dFiles is not None:
                if not self._copy_files(dFiles):
                    do_complaint_error('Unable to successfully copy '
                                        'some or all of the rulebook files')
            else:
                # something weird happened
                pass

        self._update_menu()

        # get rid of the dialog
        oConfigDialog.destroy()

    def _download_files(self, dUrls):
        """Download files from a dictionary of sName -> sURL mappings."""
        bSuccess = True
        for sName, sUrl in dUrls.items():
            if not sUrl:
                continue
            bResult = self._download_rulebook(sName, sUrl)
            bSuccess = bSuccess and bResult
        return bSuccess

    def _download_rulebook(self, sName, sUrl):
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

            return self._save_rulebook(sName, sData)
        # pylint: disable-msg=W0703
        # We really do want to catch all exceptions here
        except Exception:
            return False

    def _copy_files(self, dFiles):
        """Copy files from a dictionary of sName -> sFile mappings."""
        bSuccess = True
        for sName, sFile in dFiles.items():
            if not sFile:
                continue
            bResult = self._copy_rulebook(sName, sFile)
            bSuccess = bSuccess and bResult
        return bSuccess

    def _copy_rulebook(self, sName, sFile):
        """Copy the rulebook from a local file."""
        try:
            oFile = WwFile(sFile).open()
            sData = oFile.read()
            return self._save_rulebook(sName, sData)
        # pylint: disable-msg=W0703
        # We really do want to catch all exceptions here
        except Exception:
            return False

    def _save_rulebook(self, sName, sData):
        """Save the data from a rulebook to the preferences folder."""
        sData = self._clean_rulebook(sName, sData)

        ensure_dir_exists(self._sPrefsPath)
        sFile = os.path.join(self._sPrefsPath, self.LOCAL_NAMES[sName])

        oFile = file(sFile, 'wb')
        oFile.write(sData)
        oFile.close()

        if os.path.isfile(sFile):
            return True
        return False

    @staticmethod
    def _clean_rulebook_tags(sData):
        """Clean up the tags in the rulebook HTML"""
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

        return sData

    # pylint: disable-msg=R0914
    # We use several local variables for clarity
    def _clean_rulebook(self, sName, sData):
        """Clean up rulebook HTML"""
        sData = self._clean_rulebook_tags(sData)

        # in rulings, remove everything between header and first
        # end of first style tag
        if sName in ("Rulings", "Imbued Rules", "V:EKN Tournament Rules",
            "V:TES Complete Rules Reference"):
            oHdrToStyle = re.compile(r"</head>.*?</style>",
                re.MULTILINE | re.DOTALL)
            sData = oHdrToStyle.sub("</head>", sData, 1)

        # remove <script> tags since they're not
        # vital to the rulebook and avoid attempts by the
        # browser to access the network
        oTagRemove = re.compile(r"<script[^<>]*>[^<]*"
            r"(</script[^<>]*>)?",
            re.MULTILINE)
        sData = oTagRemove.sub("", sData)
        # remove <img> tags. These are not closed properly
        oTagRemove = re.compile(r"<img[^<>]*>")
        sData = oTagRemove.sub("", sData)
        # remove the onclick tags from the imbued rules, since they're
        # just broken
        oClickRemove = re.compile(r'\(?<a href="(images|#)[^>]*onclick=.*>'
            r'.*</a>\)?',
            re.MULTILINE)
        sData = oClickRemove.sub("", sData)

        # unclosed <a name=...>
        oUnclosedName = re.compile(r"(<a name=[^>]*>[^<>]*"
            r"<h.>[^<>]*</h.>[^<>]*)<p>",
            re.MULTILINE)

        sData = oUnclosedName.sub(r"\g<1></a><p>", sData)

        # base url for href's that begin with . or /
        sFullUrl = self.WW_RULEBOOK_URLS[sName]
        sBaseUrl = sFullUrl.rsplit("/", 1)[0]
        oHref = re.compile(r"(?P<start>href=[\"'])(?P<href>[^\"']*)"
                            r"(?P<end>[\"'])")

        def apply_base_url(oMatch):
            """Apply a base url to hrefs that start with . or /"""
            sHref = oMatch.group("href")
            if sHref.startswith(".") or sHref.startswith("/"):
                sHref = urllib.basejoin(sBaseUrl, sHref)
            return oMatch.group("start") + sHref + oMatch.group("end")

        sData = oHref.sub(apply_base_url, sData)

        # translate rulebook URLs to local links
        for sName, sUrl in self.WW_RULEBOOK_URLS.items():
            sLocal = self.LOCAL_NAMES[sName]
            sData = sData.replace(sUrl, sLocal)

        return sData

# pylint: disable-msg=C0103
# shut up complaint about the name
plugin = RulebookPlugin
