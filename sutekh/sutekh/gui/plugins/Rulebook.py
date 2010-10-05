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
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.FileOrUrlWidget import FileOrUrlWidget
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.SutekhUtility import prefs_dir, ensure_dir_exists


class RulebookConfigDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # R0904 - gtk Widget, so has many public methods
    """Dialog for configuring the Rulebook plugin."""

    POSSIBLE_FILES = [
            "Rulebook", "Imbued Rules", "Rulings", "V:EKN Tournament Rules",
            "VTES FAQ", "Imbued FAQ", "V:TES Complete Rules Reference",
    ]

    WW_RULEBOOK_URLS = {
        "Rulebook": "http://www.white-wolf.com/vtes/rulebook/rulebook.html",
        "Imbued Rules":
           "http://www.white-wolf.com/vtes/?line=Checklist_NightsOfReckoning",
        "Rulings": "http://www.white-wolf.com/vtes/index.php?line=rulings",
        "V:EKN Tournament Rules":
           "http://www.white-wolf.com/vtes/index.php?line=veknRules",
        "VTES FAQ": "http://www.thelasombra.com/vtes_faq.htm",
        "Imbued FAQ": "http://www.thelasombra.com/faq_imbued.htm",
        "V:TES Complete Rules Reference":
           "http://www.white-wolf.com/vtes/?line=outline",
    }

    def __init__(self, oParent, bFirstTime=False):
        super(RulebookConfigDialog, self).__init__('Configure Rulebook Plugin',
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL))

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.set_spacing(10)

        oDescLabel = gtk.Label()
        if not bFirstTime:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook '
                    'plugin</b>')
        else:
            oDescLabel.set_markup('<b>Choose how to configure the rulebook '
                    'plugin</b>\nChoose cancel to skip configuring the '
                    'plugin\nYou will not be prompted again')

        self._dFileSelectors = {}
        for sName in self.POSSIBLE_FILES:
            if sName in ['VTES FAQ', 'Imbued FAQ']:
                sBaseUrl = 'www.thelasombra.com'
            else:
                sBaseUrl = 'www.white-wolf.com'
            oFileSelector = FileOrUrlWidget(oParent,
                dUrls={
                    sBaseUrl: self.WW_RULEBOOK_URLS[sName],
                },
                sTitle="Select %s HTML file ..." % (sName,),
            )
            self._dFileSelectors[sName] = oFileSelector

        # pylint: disable-msg=E1101
        # pylint doesn't pick up vbox methods correctly
        self.vbox.pack_start(oDescLabel, False, False)
        for oFileSelector in self._dFileSelectors.values():
            self.vbox.pack_start(oFileSelector, False, False)

        self.show_all()

    def get_names(self):
        """Return the names that can be passed to .get_wwfile_data(...).

           Omits names where it looks like the user has not selected anything.
           """
        return [sName for sName, oSelector in self._dFileSelectors.items()
                if oSelector.get_file_or_url()[0]]

    def get_wwfile_data(self, sName):
        """Return the data for the given name."""
        return self._dFileSelectors[sName].get_wwfile_data()


class RulebookPlugin(SutekhPlugin):
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
        "VTES FAQ": "faq.html",
        "Imbued FAQ": "imbued_faq.html",
        "V:TES Complete Rules Reference": "rules_reference.html",
    }

    # pylint: disable-msg=W0142
    # ** magic OK here
    def __init__(self, *args, **kwargs):
        super(RulebookPlugin, self).__init__(*args, **kwargs)
        self._oRulebookDlg = None
        self._dMenuItems = None
        self._sPrefsPath = os.path.join(prefs_dir('Sutekh'), 'rulebook')

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow if the files can be found.
           """
        if not self.check_versions() or not self.check_model_type():
            return None

        oConfigMenuItem = gtk.MenuItem("Download Rulebook Files")
        oConfigMenuItem.connect("activate", self.config_activate)

        aMenuList = [('Data Downloads', oConfigMenuItem)]

        self._dMenuItems = {}
        for sName in self.POSSIBLE_FILES:
            oItem = gtk.MenuItem(sName)
            oItem.connect("activate", self.rulebook_activate, sName)
            self._dMenuItems[sName] = oItem
            # Add to top-level rulebook menu
            aMenuList.append(('Rulebook', oItem))

        self._update_menu()

        return aMenuList

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

    def config_activate(self, _oMenuWidget):
        """Launch the configuration dialog."""
        oDialog = RulebookConfigDialog(self.parent, False)
        self.handle_config_response(oDialog)

    def rulebook_activate(self, _oMenuWidget, sName):
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
            bSuccess = True
            for sName in oConfigDialog.get_names():
                try:
                    bResult = self._save_rulebook(sName,
                        oConfigDialog.get_wwfile_data(sName),
                    )
                # pylint: disable-msg=W0703
                # We really do want to catch all exceptions here
                except Exception:
                    bResult = False

                bSuccess = bSuccess and bResult

            if not bSuccess:
                do_complaint_error('Unable to successfully download or copy '
                                    'some or all of the rulebook files')

        self._update_menu()

        # get rid of the dialog
        oConfigDialog.destroy()

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

plugin = RulebookPlugin
