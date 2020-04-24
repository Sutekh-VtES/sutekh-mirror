# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Export a card set to HTML."""

from gi.repository import Gtk

from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.io.WriteArdbHTML import WriteArdbHTML
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.SutekhDialog import do_complaint_error
from sutekh.base.gui.SutekhFileWidget import ExportDialog
from sutekh.base.Utility import safe_filename
from sutekh.base.gui.GuiCardSetFunctions import write_cs_to_file


class CardSetExportHTML(SutekhPlugin):
    """Export a Card set to a 'nice' HTML file.

       We create a ElementTree that represents the XHTML file,
       and then dump that to file.
       This tries to match the HTML file produced by ARDB.
       """
    dTableVersions = {PhysicalCardSet: (4, 5, 6, 7)}
    aModelsSupported = (PhysicalCardSet, "MainWindow")

    dGlobalConfig = {
        'HTML export mode': 'string(default=None)',
    }

    def get_menu_item(self):
        """Register on the Plugins Menu"""
        if self._cModelType == "MainWindow":
            oPrefs = Gtk.MenuItem(label="Export to HTML preferences")
            oSubMenu = Gtk.Menu()
            oPrefs.set_submenu(oSubMenu)
            oGroup = None
            sDefault = self.get_config_item('HTML export mode')
            if sDefault is None:
                sDefault = 'Secret Library'
                self.set_config_item('HTML export mode',
                                     sDefault)
            for sString, sVal in (("Add links to The Secret Library",
                                   'Secret Library'),
                                  ("Add links to VTES Monger", 'Monger'),
                                  ("Don't add links in the HTML file",
                                   'None')):
                oItem = Gtk.RadioMenuItem(group=oGroup, label=sString)
                if not oGroup:
                    oGroup = oItem
                oSubMenu.add(oItem)
                oItem.set_active(False)
                if sVal == sDefault:
                    oItem.set_active(True)
                oItem.connect("toggled", self.change_prefs, sVal)
            return ('File Preferences', oPrefs)

        oExport = Gtk.MenuItem(label="Export to HTML")
        oExport.connect("activate", self.activate)
        return ('Export Card Set', oExport)

    def activate(self, _oWidget):
        """In response to the menu, create the dialog and run it."""
        oDlg = self.make_dialog()
        oDlg.run()
        self.handle_response(oDlg.get_name())

    def change_prefs(self, _oWidget, sChoice):
        """Manage the preferences (library to link to, etc.)"""
        sCur = self.get_config_item('HTML export mode')
        if sChoice != sCur:
            self.set_config_item('HTML export mode',
                                 sChoice)

    # pylint: disable=attribute-defined-outside-init
    # we define attributes outside __init__, but it's OK because of plugin
    # structure
    def make_dialog(self):
        """Create the dialog prompted for the filename."""
        oDlg = ExportDialog("Filename to save as", self.parent,
                            '%s.html' % safe_filename(self.view.sSetName))
        oDlg.add_filter_with_pattern('HTML Files', ['*.html'])
        # pylint: disable=no-member
        # vbox confuses pylint
        self.oTextButton = Gtk.CheckButton(label="Include Card _Texts?")
        self.oTextButton.set_active(False)
        oDlg.vbox.pack_start(self.oTextButton, False, False, 0)
        oDlg.show_all()
        return oDlg

    # pylint: enable=attribute-defined-outside-init

    def handle_response(self, sFileName):
        """Handle the response to the dialog"""
        # pylint: disable=no-member
        # SQLObject methods confuse pylint
        if sFileName is not None:
            # pylint: disable=broad-except
            # we do want to catch all exceptions here
            oCardSet = self._get_card_set()
            if not oCardSet:
                do_complaint_error("Unsupported Card Set Type")
                return
            bDoText = False
            if self.oTextButton.get_active():
                bDoText = True
            sLinkMode = self.get_config_item('HTML export mode')
            oWriter = WriteArdbHTML(sLinkMode, bDoText)
            write_cs_to_file(oCardSet, oWriter, sFileName)


plugin = CardSetExportHTML
