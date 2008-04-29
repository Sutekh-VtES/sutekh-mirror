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
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.gui.PropDialog import PropDialog
from sutekh.io.XmlFileHandling import AbstractCardSetXmlFile, \
        PhysicalCardSetXmlFile
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog
from sutekh.gui.PaneMenu import EditableCardListMenu

class CardSetMenu(EditableCardListMenu):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Card Set Menu.

       Provide the usual menu options, and implement several of the
       card set specific actions - editing card set properties, editng
       annotations, exporting to file, and so on.
       """
    # pylint: disable-msg=R0902
    # R0902 - we are keeping a lot of state, so many instance variables
    def __init__(self, oFrame, oController, oWindow, oView, sName):
        super(CardSetMenu, self).__init__(oFrame, oWindow, oController)
        self.__oView = oView
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
        self.__oProperties = self.create_menu_item(
                "Edit Card Set (%s) properties" % self.sSetName, oMenu,
                self._edit_properties)
        self.create_menu_item(
                "Edit Annotations for Card Set (%s)" % self.sSetName, oMenu,
                self._edit_annotations)
        self.__oExport = self.create_menu_item(
                "Export Card Set (%s) to File" % self.sSetName, oMenu,
                self._do_export)

        self.add_common_actions(oMenu)

        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menu_item attributes
        # (or maybe gtk.Action)
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

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature for the following methods
    def _edit_properties(self, oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        oCS = PhysicalCardSet.byName(self.sSetName)
        oProp = PropDialog(self._oMainWindow, oCS)
        oProp.run()
        (sName, sAuthor, sComment) = oProp.get_data()
        if sName is not None and sName != self.sSetName and len(sName)>0:
            # Check new name is not in use
            oNameList = PhysicalCardSet.selectBy(name=sName)
            if oNameList.count()>0:
                do_complaint_error("Chosen Card Set Name is already in use")
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

    # pylint: enable-msg=W0613
