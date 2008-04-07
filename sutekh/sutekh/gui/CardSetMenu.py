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

class CardSetMenu(gtk.MenuBar, object):
    # pylint: disable-msg=R0904
    # gtk.Widget, so menu public methods
    """Card Set Menu.

       Provide the usual menu options, and implement several of the
       card set specific actions - editing card set properties, editng
       annotations, exporting to file, and so on.
       """
    def __init__(self, oFrame, oController, oWindow, oView, sName, cType):
        super(CardSetMenu, self).__init__()
        self.__oController = oController
        self.__oWindow = oWindow
        self.__oView = oView
        self.__oFrame = oFrame
        self.sSetName = sName
        self.__cSetType = cType
        if cType is AbstractCardSet:
            self.__sMenuType = 'Abstract'
        else:
            self.__sMenuType = 'Physical'
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
        self.__iProperties = gtk.MenuItem("Edit Card Set (%s) properties" %
                self.sSetName)
        oMenu.add(self.__iProperties)
        self.__iProperties.connect('activate', self._edit_properites)
        self.__iEditAnn = gtk.MenuItem("Edit Annotations for Card Set (%s)" %
                self.sSetName)
        oMenu.add(self.__iEditAnn)
        self.__iEditAnn.connect('activate', self._edit_annotations)
        self.__iExport = gtk.MenuItem("Export Card Set (%s) to File" %
                self.sSetName)
        oMenu.add(self.__iExport)
        self.__iExport.connect('activate', self._do_export)

        iExpand = gtk.MenuItem("Expand All (Ctrl+)")
        oMenu.add(iExpand)
        iExpand.connect("activate", self._expand_all)

        iCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        oMenu.add(iCollapse)
        iCollapse.connect("activate", self._collapse_all)

        self.__iClose = gtk.MenuItem("Remove This Pane")
        oMenu.add(self.__iClose)
        self.__iClose.connect("activate", self.__oFrame.close_menu_item)
        self.__iDelete = gtk.MenuItem("Delete Card Set ("+self.sSetName+")")
        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menuitem attributes
        # (or maybe gtk.Action)
        if self.__cSetType is PhysicalCardSet:
            oSep = gtk.SeparatorMenuItem()
            oMenu.add(oSep)
            self.iViewExpansions = gtk.CheckMenuItem('Show Card Expansions'
                    ' in the Pane')
            self.iViewExpansions.set_inconsistent(False)
            self.iViewExpansions.set_active(True)
            self.iViewExpansions.connect('toggled', self._toggle_expansion)
            oMenu.add(self.iViewExpansions)

        self.iEditable = gtk.CheckMenuItem('Card Set is Editable')
        self.iEditable.set_inconsistent(False)
        self.iEditable.set_active(False)
        self.iEditable.connect('toggled', self._toggle_editable)
        self.__oController.view.set_edit_menu_item(self.iEditable)
        oMenu.add(self.iEditable)

        oSep = gtk.SeparatorMenuItem()
        oMenu.add(oSep)
        self.__iDelete.connect("activate", self._card_set_delete)
        oMenu.add(self.__iDelete)

        oMenuItem.set_submenu(oMenu)
        self.add(oMenuItem)

    def __update_card_set_menu(self):
        """Update the menu to reflect changes in the card set name."""
        self.__iProperties.get_child().set_label("Edit Card Set (%s)"
                " properties" % self.sSetName)
        self.__iExport.get_child().set_label("Export Card Set (%s) to File" %
                self.sSetName)
        self.__iDelete.get_child().set_label("Delete Card Set (%s)" %
                self.sSetName)

    def __create_filter_menu(self):
        """Create the Filter Menu."""
        # setup sub menun
        oMenuItem = gtk.MenuItem("Filter")
        oMenu = gtk.Menu()
        self.__dMenus["Filter"] = oMenu

        # items
        iFilter = gtk.MenuItem("Specify Filter")
        oMenu.add(iFilter)
        iFilter.connect('activate', self._set_active_filter)
        self.iApply = gtk.CheckMenuItem("Apply Filter")
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        oMenu.add(self.iApply)
        self.iApply.connect('toggled', self._toggle_apply_filter)
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
        for oPlugin in self.__oFrame._aPlugins:
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
                        % self.__sMenuType)
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
        oFileChooser = ExportDialog("Save %s Card Set As " % self.__sMenuType,
                self.__oWindow)
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
        self.__oFrame.deleteCardSet()

    def _toggle_apply_filter(self, oWidget):
        """Toggle the filter applied state."""
        self.__oController.view.runFilter(oWidget.active)

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
        self.__oController.view.getFilter(self)

    def _expand_all(self, oWidget):
        """Expand all the rows in the card set."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all the rows in the card set."""
        self.__oController.view.collapse_all()
    # pylint: enable-msg=W0613

    def setApplyFilter(self, bState):
        """Set the applied filter state to bState."""
        self.iApply.set_active(bState)


