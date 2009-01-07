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
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from sutekh.gui.PaneMenu import CardListMenu
from sutekh.gui.CardSetListModel import NO_SECOND_LEVEL, SHOW_EXPANSIONS, \
        SHOW_CARD_SETS, EXPANSIONS_AND_CARD_SETS, CARD_SETS_AND_EXPANSIONS, \
        THIS_SET_ONLY, ALL_CARDS, PARENT_CARDS, CHILD_CARDS, \
        IGNORE_PARENT, PARENT_COUNT, MINUS_THIS_SET, MINUS_SETS_IN_USE

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
        self.create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu('_Plugins', self._oFrame)

    # pylint: disable-msg=W0201
    # these methods are called from __init__, so it's OK
    def __create_card_set_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu(self, '_Actions')
        self.create_menu_item("Edit Card Set _Properties", oMenu,
                self._edit_properties)
        self.create_menu_item("_Save Card Set to File", oMenu,
                self._do_export)
        # Submenu for plugins
        self.create_submenu(oMenu, "_Export Card Set")
        oMenu.add(gtk.SeparatorMenuItem())
        oCountMenu = self.create_menu_item_with_submenu(oMenu,
                "Cards To Show").get_submenu()
        oThisCardSet = None
        for sString, iValue in [
                ("This Card Set Only", THIS_SET_ONLY),
                ("Show All Cards", ALL_CARDS),
                ("Show all cards in parent card set", PARENT_CARDS),
                ("Show all cards in child card sets", CHILD_CARDS),
                ]:
            oItem = gtk.RadioMenuItem(oThisCardSet, sString)
            if not oThisCardSet:
                oThisCardSet = oItem
            if self.__oController.model.iShowCardMode == iValue:
                oItem.set_active(True)
            oCountMenu.add(oItem)
            oItem.connect("toggled", self._change_count_mode, iValue)
        oModeMenu = self.create_menu_item_with_submenu(oMenu,
                "Display Mode").get_submenu()
        oNoChildren = None
        for sString, iValue in [
                ("Show No Children", NO_SECOND_LEVEL),
                ("Show Expansions", SHOW_EXPANSIONS),
                ("Show Child Card Sets", SHOW_CARD_SETS),
                ("Show Expansions and Child Card Sets",
                    EXPANSIONS_AND_CARD_SETS),
                ("Show Child Card Sets and Expansions",
                    CARD_SETS_AND_EXPANSIONS),
                ]:
            oItem = gtk.RadioMenuItem(oNoChildren, sString)
            if not oNoChildren:
                oNoChildren = oItem
            if self.__oController.model.iExtraLevelsMode == iValue:
                oItem.set_active(True)
            oModeMenu.add(oItem)
            oItem.connect("toggled", self._change_mode, iValue)

        self._oParentCol = self.create_menu_item_with_submenu(oMenu,
                "Parent Card Count")
        oParentCountMenu = self._oParentCol.get_submenu()
        oNoParentCount = None
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        oCS = PhysicalCardSet.byName(self.sSetName)
        for sString, iValue in [
                ("Don't show parent card counts", IGNORE_PARENT),
                ("Show Parent Count", PARENT_COUNT),
                ("Show difference between Parent Count and this card set",
                    MINUS_THIS_SET),
                ("Show difference between Parent Count and card sets in use",
                    MINUS_SETS_IN_USE),
                ]:
            # Should we have some way of restoring setting from last session?
            oItem = gtk.RadioMenuItem(oNoParentCount, sString)
            if not oNoParentCount:
                oNoParentCount = oItem
            if iValue == PARENT_COUNT:
                self._oDefaultParentCount = oItem
            if self.__oController.model.iParentCountMode == iValue and \
                    oCS.parent:
                oItem.set_active(True)
                self._change_parent_count_mode(oItem, iValue, True)
            elif not oCS.parent and iValue == IGNORE_PARENT:
                self._oParentCol.set_sensitive(False)
                oItem.set_active(True)
                self._change_parent_count_mode(oItem, iValue, True)
            oParentCountMenu.add(oItem)
            oItem.connect("toggled", self._change_parent_count_mode, iValue,
                    False)

        self.create_check_menu_item('Show icons for the grouping',
                oMenu, self.__oController.toggle_icons, True)

        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

        oMenu.add(gtk.SeparatorMenuItem())
        self.create_menu_item("Delete Card Set", oMenu, self._card_set_delete)

    def create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu(self, "_Edit")
        self._oEditable = self.create_check_menu_item('Card Set is Editable',
                oMenu, self.toggle_editable, False, '<Ctrl>e')
        self._oController.view.set_menu(self)
        self.create_menu_item('Copy selection', oMenu, self.copy_selection,
                '<Ctrl>c')
        self._oPaste = self.create_menu_item('Paste', oMenu,
                self._paste_selection, '<Ctrl>v')
        self._oDel = self.create_menu_item('Delete selection', oMenu,
                self._del_selection, 'Delete')
        self._oPaste.set_sensitive(False)
        self._oDel.set_sensitive(False)
        self.add_edit_menu_actions(oMenu)

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature for the following methods
    def _edit_properties(self, oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        self._oController.edit_properties(self)

    def update_card_set_menu(self, oCardSet):
        """Update the menu to reflect changes in the card set name."""
        self.sSetName = oCardSet.name
        self._oFrame.update_name(self.sSetName)

    def check_parent_count_column(self, oOldParent, oNewParent):
        """Check that the parent column values are set correctly
           when the parent changes.
           """
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        # We rely on signal handler to cause reload
        if oNewParent:
            self._oParentCol.set_sensitive(True)
            if not oOldParent:
                # Parent has changed from none, so set to default
                self._change_parent_count_mode(None, PARENT_COUNT, True)
                # Check below will force reload anyway
                self._oDefaultParentCount.set_active(True)
        else:
            self._oParentCol.set_sensitive(False)
            self._change_parent_count_mode(None, IGNORE_PARENT, True)

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
        self._oController.delete_card_set()

    def _change_mode(self, oWidget, iLevel):
        """Set which extra information is shown."""
        # NB. gtk calls this twice, once for the current value,
        # and once for the new value. We don't want to call
        # load multiple times, so this logic
        if self._oController.model.iExtraLevelsMode != iLevel:
            self._oController.model.iExtraLevelsMode = iLevel
            self._oController.view.reload_keep_expanded()

    def _change_count_mode(self, oWidget, iLevel):
        """Set which extra information is shown."""
        if self._oController.model.iShowCardMode != iLevel:
            self._oController.model.iShowCardMode = iLevel
            self._oController.view.reload_keep_expanded()

    def _change_parent_count_mode(self, oWidget, iLevel, bNoReload=False):
        """Toggle the visibility of the parent col"""
        if iLevel == IGNORE_PARENT:
            self._oController.view.set_parent_count_col_vis(False)
        else:
            self._oController.view.set_parent_count_col_vis(True)
        if self._oController.model.iParentCountMode == iLevel:
            return
        self._oController.model.iParentCountMode = iLevel
        if not bNoReload:
            self._oController.view.reload_keep_expanded()

    def toggle_editable(self, oWidget):
        """Toggle the editable state of the card set."""
        if self._oController.model.bEditable != oWidget.active:
            self._oController.view.toggle_editable(oWidget.active)
            self._oPaste.set_sensitive(oWidget.active)
            self._oDel.set_sensitive(oWidget.active)

    def force_editable_mode(self, bValue):
        """Toggle the editable state of the card set."""
        self._oEditable.set_active(bValue)
        self._oPaste.set_sensitive(bValue)
        self._oDel.set_sensitive(bValue)

    def _del_selection(self, oWidget):
        """Delete the current selection"""
        self._oController.view.del_selection()

    def _paste_selection(self, oWidget):
        """Try to paste the current clipbaord contents"""
        self._oController.view.do_paste()

    # pylint: enable-msg=W0613
