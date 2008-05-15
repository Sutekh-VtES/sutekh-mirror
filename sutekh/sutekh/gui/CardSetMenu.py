# CardSetMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set pane"""

import gtk
from sutekh.SutekhUtility import safe_filename
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog
from sutekh.gui.PaneMenu import CardListMenu

class CardSetMenu(CardListMenu):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Card Set Menu.

       Provide the usual menu options, and implement several of the
       card set specific actions - editing card set properties, editng
       annotations, exporting to file, and so on.
       """
    # pylint: disable-msg=R0902
    # R0902 - we are keeping a lot of state, so many instance variables
    def __init__(self, oFrame, oController, oWindow, sName):
        super(CardSetMenu, self).__init__(oFrame, oWindow, oController)
        self.__oController = oController
        self.sSetName = sName
        self.__create_card_set_menu()
        self._create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu('_Plugins', self._oFrame)

    # pylint: disable-msg=W0201
    # these methods are called from __init__, so it's OK
    def __create_card_set_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu(self, '_Actions')
        self.__oProperties = self.create_menu_item(
                "Edit Card Set (%s) properties" % self.sSetName, oMenu,
                self._edit_properties)
        self.create_menu_item(
                "Edit Annotations for Card Set (%s)" % self.sSetName, oMenu,
                self._edit_annotations)
        self.__oExport = self.create_menu_item(
                "Export Card Set (%s) to File" % self.sSetName, oMenu,
                self._do_export)

        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menu_item attributes
        # (or maybe gtk.Action)
        oMenu.add(gtk.SeparatorMenuItem())
        self.create_check_menu_item('Show Card Expansions',
                oMenu, self._toggle_expansion, True)
        self.create_check_menu_item('Show Cards with Count of 0', oMenu,
                self._toggle_all_abstract_cards,
                self._oController.model.bAddAllAbstractCards)

        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

        oMenu.add(gtk.SeparatorMenuItem())
        self.create_menu_item("Delete Card Set", oMenu, self._card_set_delete)

    def __update_card_set_menu(self):
        """Update the menu to reflect changes in the card set name."""
        self.__oProperties.get_child().set_label("Edit Card Set (%s)"
                " properties" % self.sSetName)
        self.__oExport.get_child().set_label("Export Card Set (%s) to File" %
                self.sSetName)

    def _create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu(self, "_Edit")
        oEditable = self.create_check_menu_item('Card Set is Editable', oMenu,
                self.toggle_editable, False, '<Ctrl>e')
        self._oController.view.set_edit_menu_item(oEditable)
        self.create_menu_item('Copy selection', oMenu, self.copy_selection,
                '<Ctrl>c')
        self.create_menu_item('Paste', oMenu, self._paste_selection, '<Ctrl>v')
        self.create_menu_item('Delete selection', oMenu, self._del_selection,
                'Delete')

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature for the following methods
    def _edit_properties(self, oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        oCS = PhysicalCardSet.byName(self.sSetName)
        oProp = CreateCardSetDialog(self._oMainWindow, oCardSet=oCS)
        oProp.run()
        sName = oProp.get_name()
        if sName:
            # Passed, so update the card set
            oCS.name = sName
            self.__oController.view.sSetName = sName
            self.sSetName = sName
            self._oFrame.update_name(self.sSetName)
            sAuthor = oProp.get_author()
            sComment = oProp.get_comment()
            oParent = oProp.get_parent()
            if sAuthor is not None:
                oCS.author = sAuthor
            if sComment is not None:
                oCS.comment = sComment
            if oParent != oCS.parent:
                oCS.parent = oParent
            if oCS.parent:
                self._oController.view.set_parent_count_col_vis(True)
            else:
                self._oController.view.set_parent_count_col_vis(False)
            self.__update_card_set_menu()
            oCS.syncUpdate()
            # We may well have changed stuff on the card list pane, so reload
            self._oMainWindow.reload_pcs_list()

    def _edit_annotations(self, oWidget):
        """Popup the Edit Annotations dialog."""
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        oCS = PhysicalCardSet.byName(self.sSetName)
        oEditAnn = EditAnnotationsDialog("Edit Annotations of Card Set (%s)" %
                self.sSetName, self._oMainWindow, oCS.name, oCS.annotations)
        oEditAnn.run()
        oCS.annotations = oEditAnn.get_data()
        oCS.syncUpdate()

    def _do_export(self, oWidget):
        """Export the card set to the chosen filename."""
        oFileChooser = ExportDialog("Save Card Set As ", self._oMainWindow,
                '%s.xml' % safe_filename(self.sSetName))
        oFileChooser.add_filter_with_pattern('XML Files', ['*.xml'])
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            # User has OK'd us overwriting anything
            oWriter = PhysicalCardSetXmlFile(sFileName)
            oWriter.write(self.sSetName)

    def _card_set_delete(self, oWidget):
        """Delete the card set."""
        self._oFrame.delete_card_set()

    def _toggle_expansion(self, oWidget):
        """Toggle whether Expansion information is shown."""
        self._oController.model.bExpansions = oWidget.active
        self._oController.view.reload_keep_expanded()

    def _toggle_all_abstract_cards(self, oWidget):
        """Toggle the display of cards with a count of 0 in the card list."""
        self._oController.model.bAddAllAbstractCards = oWidget.active
        self._oMainWindow.config_file.set_show_zero_count_cards(
                oWidget.active)
        self._oController.view.reload_keep_expanded()

    def toggle_editable(self, oWidget):
        """Toggle the editable state of the card set."""
        if self._oController.model.bEditable != oWidget.active:
            self._oController.view.toggle_editable(oWidget.active)

    def _del_selection(self, oWidget):
        """Delete the current selection"""
        self._oController.view.del_selection()

    def _paste_selection(self, oWidget):
        """Try to paste the current clipbaord contents"""
        self._oController.view.do_paste()

    # pylint: enable-msg=W0613

class EditableCardListMenu(CardListMenu):
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods
    """Base class for Editable Card List Menus

       Adds some common methods for dealing with the card lists -
       paste selction + delete, etc.
       """
    def __init__(self, oFrame, oWindow, oController):
        super(EditableCardListMenu, self).__init__(oFrame, oWindow,
                oController)


