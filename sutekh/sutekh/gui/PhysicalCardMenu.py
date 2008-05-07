# PhysicalCardMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the Physical Card View
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Physical card collection."""

import gtk
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.gui.PaneMenu import CardListMenu
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile

class PhysicalCardMenu(CardListMenu):
    """Menu for the Physical card collection.

       Enables actions specific to the physical card collection (export to
       file, etc), filtering and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oController, oWindow):
        super(PhysicalCardMenu, self).__init__(oFrame, oWindow, oController)
        self.__create_physical_cl_menu()
        self.create_filter_menu()
        self.create_plugins_menu('_Plugins', self._oFrame)

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_physical_cl_menu(self):
        """Create the Actions menu for the card list."""
        # setup sub menu
        oMenu = self.create_submenu(self, "_Actions")

        # items
        self.create_menu_item("Export Collection to File", oMenu,
                self._do_export)
        self.create_check_menu_item('Show Card Expansions', oMenu,
                self._toggle_expansion, True)

        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def _do_export(self, oWidget):
        """Handling exporting the card list to file."""
        oFileChooser = ExportDialog("Save Collection As", self._oMainWindow,
                'MyCollection.xml')
        oFileChooser.add_filter_with_pattern('XML Files', ['*.xml'])
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            oWriter = PhysicalCardXmlFile(sFileName)
            oWriter.write()

    def _toggle_expansion(self, oWidget):
        """Toggle whether the expansion information is shown."""
        self._oController.model.bExpansions = oWidget.active
        self._oController.view.reload_keep_expanded()

    # pylint: enable-msg=W0613
