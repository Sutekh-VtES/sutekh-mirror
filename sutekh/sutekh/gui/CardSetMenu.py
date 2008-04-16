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
from sutekh.gui.PaneMenu import PaneMenu

def _type_to_string(cSetType):
    """Convert the class SetType to a string for the menus"""
    if cSetType is AbstractCardSet:
        return 'Abstract'
    else:
        return 'Physical'

class CardSetMenu(PaneMenu, object):
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
        super(CardSetMenu, self).__init__(oFrame, oWindow)
        self.__oController = oController
        self.__oView = oView
        self.sSetName = sName
        self.__cSetType = cType
        self.__create_card_set_menu()
        self.__create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu()

    # pylint: disable-msg=W0201
    # these methods are called from __init__, so it's OK
    def __create_card_set_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu('Actions')
        self.__oProperties = self.create_menu_item(
                "Edit Card Set (%s) properties" % self.sSetName, oMenu,
                self._edit_properties)
        self.create_menu_item(
                "Edit Annotations for Card Set (%s)" % self.sSetName, oMenu,
                self._edit_annotations)
        self.__oExport = self.create_menu_item(
                "Export Card Set (%s) to File" % self.sSetName, oMenu,
                self._do_export)

        self.create_menu_item("Expand All", oMenu, self._expand_all,
                '<Ctrl>plus')
        self.create_menu_item("Collapse All", oMenu, self._collapse_all,
                '<Ctrl>minus')
        self.create_menu_item("Remove This Pane", oMenu,
                self._oFrame.close_menu_item)
        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menu_item attributes
        # (or maybe gtk.Action)
        if self.__cSetType is PhysicalCardSet:
            oMenu.add(gtk.SeparatorMenuItem())
            self.create_check_menu_item('Show Card Expansions in the Pane',
                    oMenu, self._toggle_expansion, True)
        oMenu.add(gtk.SeparatorMenuItem())
        self.create_menu_item("Delete Card Set", oMenu, self._card_set_delete)

    def __update_card_set_menu(self):
        """Update the menu to reflect changes in the card set name."""
        self.__oProperties.get_child().set_label("Edit Card Set (%s)"
                " properties" % self.sSetName)
        self.__oExport.get_child().set_label("Export Card Set (%s) to File" %
                self.sSetName)

    def __create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu("Edit")
        oEditable = self.create_check_menu_item('Card Set is Editable', oMenu,
                self._toggle_editable, False, '<Ctrl>e')
        self.__oController.view.set_edit_menu_item(oEditable)
        self.create_menu_item('Copy selection', oMenu, self._copy_selection,
                '<Ctrl>c')
        self.create_menu_item('Paste', oMenu, self._paste_selection, '<Ctrl>v')
        self.create_menu_item('Delete selection', oMenu, self._del_selection,
                'Delete')

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature for the following methods
    def _edit_properties(self, oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        oCS = self.__cSetType.byName(self.sSetName)
        oProp = PropDialog(self._oMainWindow, oCS)
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
                self._oFrame.update_name(self.sSetName)
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
                self.sSetName, self._oMainWindow, oCS.name, oCS.annotations)
        oEditAnn.run()
        oCS.annotations = oEditAnn.get_data()
        oCS.syncUpdate()

    def _do_export(self, oWidget):
        """Export the card set to the chosen filename."""
        oFileChooser = ExportDialog("Save %s Card Set As " %
                _type_to_string(self.__cSetType), self._oMainWindow)
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
        self._oFrame.delete_card_set()

    def toggle_apply_filter(self, oWidget):
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

    def set_active_filter(self, oWidget):
        """Set the current filter for the card set."""
        self.__oController.view.get_filter(self)

    def _expand_all(self, oWidget):
        """Expand all the rows in the card set."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all the rows in the card set."""
        self.__oController.view.collapse_all()

    def _del_selection(self, oWidget):
        """Delete the current selection"""
        self.__oController.view.del_selection()

    def _copy_selection(self, oWidget):
        """Copy the current selection to the application clipboard."""
        self.__oController.view.copy_selection()

    def _paste_selection(self, oWidget):
        """Try to paste the current clipbaord contents"""
        self.__oController.view.do_paste()

    # pylint: enable-msg=W0613
