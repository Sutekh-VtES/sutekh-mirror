# FilterEditor.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Editor component for generic filter ASTs.
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for editing filters."""

from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.FilterModelPanes import FilterModelPanes, add_accel_to_button
from sutekh.core.FilterParser import get_filters_for_type
import gtk
import pango


class FilterEditor(gtk.Alignment):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """GTK component for editing Sutekh filter ASTs.

       Provides a graphical representation of the filter as nested boxes,
       which the user can extend or remove from.
       """
    def __init__(self, oAST, sFilterType, oParser, oFilterDialog):
        # Child widget absorbs all free space
        super(FilterEditor, self).__init__(xscale=1.0, yscale=1.0)
        self.__oParser = oParser
        self.__oFilterDialog = oFilterDialog  # Dialog we're a child of

        self.__oPanes = FilterModelPanes(sFilterType, oFilterDialog)

        self.__sFilterType = sFilterType

        oNameLabel = gtk.Label("Filter name:")
        self.__oNameEntry = gtk.Entry()
        self.__oNameEntry.set_width_chars(30)

        oHelpButton = gtk.Button("Help")
        oHelpButton.connect("clicked", self.__show_help_dialog)
        add_accel_to_button(oHelpButton, 'F1', oFilterDialog.accel_group)

        oHBox = gtk.HBox(spacing=5)
        oHBox.pack_start(oNameLabel, expand=False)
        oHBox.pack_start(self.__oNameEntry, expand=False)
        oHBox.pack_end(oHelpButton, expand=False)

        self.__oVBox = gtk.VBox(spacing=5)
        self.__oVBox.pack_end(oHBox, expand=False)
        self.__oVBox.pack_end(gtk.HSeparator(), expand=False)
        self.__oVBox.pack_start(self.__oPanes, expand=True)

        self.add(self.__oVBox)

        self.replace_ast(oAST)

    def get_filter(self):
        """Get the actual filter for the current AST."""
        oAST = self.get_current_ast()
        if oAST is None:
            return None
        else:
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
        oDlg = SutekhDialog("Help on Filters", self.__oFilterDialog,
                gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        oDlg.set_default_size(600, 500)
        # pylint: disable-msg=E1101
        # vbox confuse pylint

        # Ensure we sort this in the same order as the toolbar
        oHelpView = AutoScrolledWindow(FilterHelpTextView(
            sorted(get_filters_for_type(self.__sFilterType),
                key=lambda x: x.description)))
        oDlg.vbox.pack_start(oHelpView)
        oDlg.show_all()

        try:
            oDlg.run()
        finally:
            oDlg.destroy()


class FilterHelpBuffer(gtk.TextBuffer):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """TextBuffer object used to display the help about the filters."""
    def __init__(self):
        super(FilterHelpBuffer, self).__init__(None)

        # See http://www.pygtk.org/pygtk2reference/class-gtktexttag.html
        # for some possible properties

        self.create_tag("header", weight=pango.WEIGHT_BOLD,
                scale=pango.SCALE_LARGE, underline=pango.UNDERLINE_SINGLE)
        self.create_tag("description", weight=pango.WEIGHT_BOLD)
        self.create_tag("keyword", style=pango.STYLE_ITALIC)
        self.create_tag("helptext", left_margin=10)
        self._oIter = self.get_iter_at_offset(0)

    # pylint: disable-msg=W0142
    # ** magic OK here
    def tag_text(self, *aArgs, **kwargs):
        """Insert text into the buffer with tags."""
        self.insert_with_tags_by_name(self._oIter, *aArgs, **kwargs)

    # pylint: enable-msg=W0142

    def add_help_text(self, sDescription, sHelpText):
        """Add the given help text to the text buffer."""
        self.tag_text(sDescription, "description")
        self.tag_text(" :\n")
        self.tag_text(sHelpText, "helptext")
        self.tag_text("\n")

    def reset_iter(self):
        """reset the iterator to the start of the buffer."""
        self._oIter = self.get_iter_at_offset(0)


class FilterHelpTextView(gtk.TextView):
    """TextView widget for displaying the help text."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, aFilterTypes):
        super(FilterHelpTextView, self).__init__()
        oBuf = FilterHelpBuffer()

        self.set_buffer(oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self.set_border_width(5)
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

        oBuf.reset_iter()

        oBuf.tag_text('Usage', 'header')
        oBuf.tag_text("\n")

        oBuf.tag_text(
            "Filter elements and values for the filters can be dragged "
            "from the right hand pane to the filter to add them to "
            "the filter, and dragged from the filter to the right hand "
            "pane to remove them from the filter. Disabled filter elements "
            "or filter elements with no values set are ignored.\n\n",
            'helptext')

        oBuf.tag_text('Keyboard Navigation', 'header')
        oBuf.tag_text("\n")

        oBuf.tag_text("You can switch between the different filter lists "
                "using <Alt>-Left and <Alt>-Right. <Ctrl>-Enter will "
                "paste the currently selected list of values into the filter. "
                "<Del> will delete a value or filter part from the filter."
                "<Ctrl>-Space will disable a filter part, while <Alt>-Space "
                "will negate it.\n\n", "helptext")

        oBuf.tag_text('Available Filter Elements', 'header')
        oBuf.tag_text("\n")

        oBuf.tag_text("The available filtering options are listed below. "
            "The first line of each item shows the description "
            "you'll see in the filter editor in bold. "
            "The rest of the description describes the arguments "
            "the filter takes and the results it produces.\n\n", "helptext")

        # Add test for filter group
        oBuf.add_help_text('Filter Group', "Filter element with holds "
                "other filter elements. The result of is the combination "
                "of all the filter elements as specified by the Filter "
                "Group type (All of, Any of and so on).")

        for oFilt in aFilterTypes:
            oBuf.add_help_text(oFilt.description,
                    oFilt.helptext)

        oBuf.tag_text("\n"
            "Note: Using filters which require information about "
            "cards in a card set will temporarily turn off displaying "
            "cards with zero counts (for modes where this is possible) "
            "in the card list since there are no "
            "associated cards on which to base the query. "
            "Filters affected by this are: Physical Expansion, "
            "Card Sets and In Card Sets in Use.")
