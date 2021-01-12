# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Editor component for generic filter ASTs.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for editing filters."""

from gi.repository import Gtk

from .FilterModelPanes import FilterModelPanes, add_accel_to_button


class FilterEditor(Gtk.Alignment):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """GTK component for editing Sutekh filter ASTs.

       Provides a graphical representation of the filter as nested boxes,
       which the user can extend or remove from.
       """
    def __init__(self, oAST, sFilterType, oParser, oFilterDialog):
        # Child widget absorbs all free space
        super().__init__(xscale=1.0, yscale=1.0)
        self.__oParser = oParser
        self.__oFilterDialog = oFilterDialog  # Dialog we're a child of

        self.__oPanes = FilterModelPanes(sFilterType, oFilterDialog)

        self.__sFilterType = sFilterType

        oNameLabel = Gtk.Label(label="Filter name:")
        self.__oNameEntry = Gtk.Entry()
        self.__oNameEntry.set_width_chars(30)

        oHelpButton = Gtk.Button("Help")
        oHelpButton.connect("clicked", self.__show_help_dialog)
        add_accel_to_button(oHelpButton, 'F1', oFilterDialog.accel_group)

        oHBox = Gtk.HBox(spacing=5)
        oHBox.pack_start(oNameLabel, False, True, 0)
        oHBox.pack_start(self.__oNameEntry, False, True, 0)
        oHBox.pack_end(oHelpButton, False, False, 0)

        self.__oVBox = Gtk.VBox(spacing=5)
        self.__oVBox.pack_end(oHBox, False, False, 0)
        self.__oVBox.pack_end(Gtk.HSeparator(), False, False, 0)
        self.__oVBox.pack_start(self.__oPanes, True, True, 0)

        self.add(self.__oVBox)

        self.replace_ast(oAST)

    def get_filter(self):
        """Get the actual filter for the current AST."""
        oAST = self.get_current_ast()
        if oAST is None:
            return None
        return oAST.get_filter()

    def get_current_ast(self):
        """Get the current AST represented by the editor."""
        return self.__oPanes.get_ast_with_values()

    def get_current_text(self):
        """Get the current text of the filter for saving in the config
           file.

           We include any current set values for the filter when saving."""
        return self.__oPanes.get_text()

    def replace_ast(self, oAST):
        """Replace the current AST with a new one and update the GUI,
           preserving variable values if possible.

           Also used to setup the filter initially.
           """
        self.__oPanes.replace_ast(oAST)

    def set_name(self, sName):
        """Set the filter name."""
        self.__oNameEntry.set_text(sName)

    def get_name(self):
        """Get the filter name."""
        return self.__oNameEntry.get_text().strip()

    def connect_name_changed(self, fCallback):
        """Connect a callback to the name entry change signal."""
        self.__oNameEntry.connect('changed', fCallback)

    def __show_help_dialog(self, _oHelpButton):
        """Show a dialog window with the helptext from the filters."""
        # FIXME: Is there a better way to find the main window
        oMainWindow = Gtk.window_list_toplevels()[0]
        if self.__sFilterType == 'PhysicalCard':
            oMainWindow.show_card_filter_help()
        elif self.__sFilterType == 'PhysicalCardSet':
            oMainWindow.show_card_set_filter_help()
        else:
            raise RuntimeError(
                'No help for unknown filter type %s' % self.__sFilterType)
