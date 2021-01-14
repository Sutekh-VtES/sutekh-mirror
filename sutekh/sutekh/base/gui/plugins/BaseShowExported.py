# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for displaying the exported version of a card set in a Gtk.TextView.
   Intended to make cutting and pasting easier."""

from io import StringIO

from gi.repository import Gdk, Gtk

from ...core.BaseTables import PhysicalCardSet
from ...core.CardSetHolder import CardSetWrapper
from ...io.WriteCSV import WriteCSV
from ..BasePluginManager import BasePlugin
from ..AutoScrolledWindow import AutoScrolledWindow
from ..SutekhDialog import SutekhDialog


class BaseShowExported(BasePlugin):
    """Display the various exported versions of a card set.

       The card set is shown in a textview, and the user can toggle between
       the different formats. This is designed to make it trivial to
       cut-n-paste the card set into something else (such as a web-browser).
       """

    dTableVersions = {}
    aModelsSupported = (PhysicalCardSet,)

    EXPORTERS = {
        # radio button text : Writer
        'CSV Export (with headers)': WriteCSV,
    }

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        oShowExported = Gtk.MenuItem(
            label="Display card set in alternative format")
        oShowExported.connect("activate", self.activate)
        return ('Actions', oShowExported)

    def activate(self, _oWidget):
        """Handle response from menu"""
        oCardSet = self._get_card_set()
        if not oCardSet:
            return
        oDlg = SutekhDialog("Exported CardSet: %s" % self.view.sSetName,
                            self.parent, Gtk.DialogFlags.DESTROY_WITH_PARENT)
        oDlg.set_default_size(700, 600)
        # Add scrolled window for text
        oTextBuffer = ExportBuffer()
        oTextView = Gtk.TextView()
        oTextView.set_buffer(oTextBuffer)
        oTextView.set_editable(False)
        oTextView.set_wrap_mode(Gtk.WrapMode.NONE)  # preserve long lines
        oTextView.set_border_width(5)
        oTextView.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse("white"))
        oDlg.vbox.pack_start(AutoScrolledWindow(oTextView), True, True, 0)
        # Add the radio buttons
        oTable = Gtk.Table(len(self.EXPORTERS) // 2, 2)
        iXPos, iYPos = 0, 0
        oFirstBut = None
        for sName in sorted(self.EXPORTERS):
            if not oFirstBut:
                oBut = Gtk.RadioButton(group=None, label=sName)
                oFirstBut = oBut
                oFirstBut.set_active(True)
                self._set_text(sName, oCardSet, oTextBuffer)
            else:
                oBut = Gtk.RadioButton(group=oFirstBut, label=sName)
            oBut.connect('toggled', self._button_toggled, sName, oCardSet,
                         oTextBuffer)
            oTable.attach(oBut, iXPos, iXPos + 1, iYPos, iYPos + 1)
            iXPos += 1
            if iXPos > 1:
                iXPos = 0
                iYPos += 1
        oDlg.vbox.pack_start(oTable, False, True, True, 0)
        oDlg.add_button("_Close", Gtk.ResponseType.CLOSE)
        oDlg.connect("response", lambda oW, oR: oDlg.destroy())
        oDlg.show_all()
        oDlg.run()

    def _button_toggled(self, oBut, sName, oCardSet, oTextBuffer):
        """Handle user changing the toggle button state"""
        if not oBut.get_active():
            # Only concerned with the button that's just become active
            return
        self._set_text(sName, oCardSet, oTextBuffer)

    def _set_text(self, sName, oCardSet, oTextBuffer):
        """Internals of setting the buffer to the correct text"""
        cWriter = self.EXPORTERS[sName]
        oWriter = cWriter()
        fOut = StringIO()
        oWriter.write(fOut, CardSetWrapper(oCardSet))
        oTextBuffer.set_text(fOut.getvalue())
        fOut.close()


class ExportBuffer(Gtk.TextBuffer):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Buffer object for showing the exported card set text"""

    def __init__(self):
        super().__init__()
        self.create_tag("text", left_margin=0)

    def set_text(self, sCardSetText):
        """Set the buffer contents to the card set text"""
        oStart, oEnd = self.get_bounds()
        self.delete(oStart, oEnd)
        oIter = self.get_iter_at_offset(0)
        self.insert_with_tags_by_name(oIter, sCardSetText, "text")
