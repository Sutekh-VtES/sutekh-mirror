# CardSetMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set pane"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.gui.ExportDialog import ExportDialog
from sutekh.gui.PropDialog import PropDialog
from sutekh.io.XmlFileHandling import AbstractCardSetXmlFile, \
        PhysicalCardSetXmlFile
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog

def _type_to_string(cSetType):
    """Convert the class SetType to a string for the menus"""
    if cSetType is AbstractCardSet:
        return 'Abstract'
    else:
        return 'Physical'

class CardSetMenu(gtk.MenuBar, object):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Card Set Menu.

       Provide the usual menu options, and implement several of the
       card set specific actions - editing card set properties, editng
       annotations, exporting to file, and so on.
       """
    # pylint: disable-msg=R0913, R0902
    # R0913 - we need all these arguments
    # R0902 - we are keeping a lot of state, so many instance variables
    def __init__(self, oFrame, oController, oWindow, oView, sName, cType):
        super(CardSetMenu, self).__init__()
        self.__oController = oController
        self.__oWindow = oWindow
        self.__oView = oView
        self.__oFrame = oFrame
        self.sSetName = sName
        self.__cSetType = cType
        self.__dMenus = {}
        self.__create_card_set_menu()
        self.__create_filter_menu()
        self.__create_plugin_menu()

    # pylint: disable-msg=W0201
    # these methods are called from __init__, so it's OK
    def __create_card_set_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenuItem = gtk.MenuItem("Actions")
        oMenu = gtk.Menu()
        self.__dMenus["Actions"] = oMenu
        self.__oProperties = gtk.MenuItem("Edit Card Set (%s) properties" %
                self.sSetName)
        oMenu.add(self.__oProperties)
        self.__oProperties.connect('activate', self._edit_properites)
        oEditAnn = gtk.MenuItem("Edit Annotations for Card Set (%s)" %
                self.sSetName)
        oMenu.add(oEditAnn)
        oEditAnn.connect('activate', self._edit_annotations)
        self.__oExport = gtk.MenuItem("Export Card Set (%s) to File" %
                self.sSetName)
        oMenu.add(self.__oExport)
        self.__oExport.connect('activate', self._do_export)

        oExpand = gtk.MenuItem("Expand All (Ctrl+)")
        oMenu.add(oExpand)
        oExpand.connect("activate", self._expand_all)

        oCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        oMenu.add(oCollapse)
        oCollapse.connect("activate", self._collapse_all)

        oClose = gtk.MenuItem("Remove This Pane")
        oMenu.add(oClose)
        oClose.connect("activate", self.__oFrame.close_menu_item)
        oDelete = gtk.MenuItem("Delete Card Set")
        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menuitem attributes
        # (or maybe gtk.Action)
        if self.__cSetType is PhysicalCardSet:
            oSep = gtk.SeparatorMenuItem()
            oMenu.add(oSep)
            oViewExpansions = gtk.CheckMenuItem('Show Card Expansions'
                    ' in the Pane')
            oViewExpansions.set_inconsistent(False)
            oViewExpansions.set_active(True)
            oViewExpansions.connect('toggled', self._toggle_expansion)
            oMenu.add(oViewExpansions)

        oEditable = gtk.CheckMenuItem('Card Set is Editable')
        oEditable.set_inconsistent(False)
        oEditable.set_active(False)
        oEditable.connect('toggled', self._toggle_editable)
        self.__oController.view.set_edit_menu_item(oEditable)
        oMenu.add(oEditable)

        oSep = gtk.SeparatorMenuItem()
        oMenu.add(oSep)
        oDelete.connect("activate", self._card_set_delete)
        oMenu.add(oDelete)

        oMenuItem.set_submenu(oMenu)
        self.add(oMenuItem)

    def __update_card_set_menu(self):
        """Update the menu to reflect changes in the card set name."""
        self.__oProperties.get_child().set_label("Edit Card Set (%s)"
                " properties" % self.sSetName)
        self.__oExport.get_child().set_label("Export Card Set (%s) to File" %
                self.sSetName)

    def __create_filter_menu(self):
        """Create the Filter Menu."""
        # setup sub menun
        oMenuItem = gtk.MenuItem("Filter")
        oMenu = gtk.Menu()
        self.__dMenus["Filter"] = oMenu

        # items
        oFilter = gtk.MenuItem("Specify Filter")
        oMenu.add(oFilter)
        oFilter.connect('activate', self._set_active_filter)
        self.oApply = gtk.CheckMenuItem("Apply Filter")
        self.oApply.set_inconsistent(False)
        self.oApply.set_active(False)
        oMenu.add(self.oApply)
        self.oApply.connect('toggled', self._toggle_apply_filter)
        # Add the Menu
        oMenuItem.set_submenu(oMenu)
        self.add(oMenuItem)

    def __create_plugin_menu(self):
        """Create the plugins menu."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Plugins")
        oMenu = gtk.Menu()
        self.__dMenus["Plugins"] = oMenu
        # plugins
        for oPlugin in self.__oFrame.plugins:
            oPlugin.add_to_menu(self.__dMenus, oMenu)
        oMenuItem.set_submenu(oMenu)
        self.add(oMenuItem)
        if len(oMenu.get_children()) == 0:
            oMenuItem.set_sensitive(False)
    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature for the following methods
    def _edit_properites(self, oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        oCS = self.__cSetType.byName(self.sSetName)
        oProp = PropDialog("Edit Card Set (" + self.sSetName + ") Propeties",
                         self.__oWindow, oCS.name, oCS.author, oCS.comment)
        oProp.run()
        (sName, sAuthor, sComment) = oProp.get_data()
        if sName is not None and sName != self.sSetName and len(sName)>0:
            # Check new name is not in use
            oNameList = self.__cSetType.selectBy(name=sName)
            if oNameList.count()>0:
                do_complaint_error("Chosen %s Card Set Name is already in use"
                        % _type_to_string(self.__cSetType))
                return
            else:
                oCS.name = sName
                self.__oView.sSetName = sName
                self.sSetName = sName
                self.__oFrame.update_name(self.sSetName)
                self.__update_card_set_menu()
                oCS.syncUpdate()
        if sAuthor is not None:
            oCS.author = sAuthor
            oCS.syncUpdate()
        if sComment is not None:
            oCS.comment = sComment
            oCS.syncUpdate()

    def _edit_annotations(self, oWidget):
        """Popup the Edit Annotations dialog."""
        oCS = self.__cSetType.byName(self.sSetName)
        oEditAnn = EditAnnotationsDialog("Edit Annotations of Card Set (%s)" %
                self.sSetName, self.__oWindow, oCS.name, oCS.annotations)
        oEditAnn.run()
        oCS.annotations = oEditAnn.get_data()
        oCS.syncUpdate()

    def _do_export(self, oWidget):
        """Export the card set to the chosen filename."""
        oFileChooser = ExportDialog("Save %s Card Set As " %
                _type_to_string(self.__cSetType), self.__oWindow)
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            # User has OK'd us overwriting anything
            if self.__cSetType is PhysicalCardSet:
                oWriter = PhysicalCardSetXmlFile(sFileName)
            else:
                oWriter = AbstractCardSetXmlFile(sFileName)
            oWriter.write(self.sSetName)

    def _card_set_delete(self, oWidget):
        """Delete the card set."""
        self.__oFrame.delete_card_set()

    def _toggle_apply_filter(self, oWidget):
        """Toggle the filter applied state."""
        self.__oController.view.run_filter(oWidget.active)

    def _toggle_expansion(self, oWidget):
        """Toggle whether Expansion information is shown."""
        self.__oController.model.bExpansions = oWidget.active
        self.__oController.view.reload_keep_expanded()

    def _toggle_editable(self, oWidget):
        """Toggle the editable state of the card set."""
        if self.__oController.model.bEditable != oWidget.active:
            self.__oController.view.toggle_editable(oWidget.active)

    def _set_active_filter(self, oWidget):
        """Set the current filter for the card set."""
        self.__oController.view.get_filter(self)

    def _expand_all(self, oWidget):
        """Expand all the rows in the card set."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all the rows in the card set."""
        self.__oController.view.collapse_all()
    # pylint: enable-msg=W0613

    def set_apply_filter(self, bState):
        """Set the applied filter state to bState."""
        self.oApply.set_active(bState)


