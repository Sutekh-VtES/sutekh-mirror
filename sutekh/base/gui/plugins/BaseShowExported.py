# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for displaying the exported version of a card set in a gtk.TextView.
   Intended to make cutting and pasting easier."""

import gtk
import StringIO
from ...core.BaseObjects import PhysicalCardSet
from ...core.CardSetHolder import CardSetWrapper
from ..BasePluginManager import BasePlugin
from ..AutoScrolledWindow import AutoScrolledWindow
from ..SutekhDialog import SutekhDialog
from ...io.WriteCSV import WriteCSV


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
        if not self._check_versions() or not self._check_model_type():
            return None
        oShowExported = gtk.MenuItem("Display card set in alternative format")
        oShowExported.connect("activate", self.activate)
        return ('Actions', oShowExported)

    def activate(self, _oWidget):
        """Handle response from menu"""
        oCardSet = self._get_card_set()
        if not oCardSet:
            return
        oDlg = SutekhDialog("Exported CardSet: %s" % self.view.sSetName,
                            self.parent, gtk.DIALOG_DESTROY_WITH_PARENT)
        oDlg.set_default_size(700, 600)
        # Add scrolled window for text
        oTextBuffer = ExportBuffer()
        oTextView = gtk.TextView()
        oTextView.set_buffer(oTextBuffer)
        oTextView.set_editable(False)
        oTextView.set_wrap_mode(gtk.WRAP_NONE)  # preserve long lines
        oTextView.set_border_width(5)
        oTextView.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        # pylint: disable=E1101
        # vbox confuses pylint
        oDlg.vbox.pack_start(AutoScrolledWindow(oTextView))
        # Add the radio buttons
        oTable = gtk.Table(len(self.EXPORTERS) // 2, 2)
        iXPos, iYPos = 0, 0
        oFirstBut = None
        for sName in sorted(self.EXPORTERS):
            if not oFirstBut:
                oBut = gtk.RadioButton(None, sName)
                oFirstBut = oBut
                oFirstBut.set_active(True)
                self._set_text(sName, oCardSet, oTextBuffer)
            else:
                oBut = gtk.RadioButton(oFirstBut, sName)
            oBut.connect('toggled', self._button_toggled, sName, oCardSet,
                         oTextBuffer)
            oTable.attach(oBut, iXPos, iXPos + 1, iYPos, iYPos + 1)
            iXPos += 1
            if iXPos > 1:
                iXPos = 0
                iYPos += 1
        oDlg.vbox.pack_start(oTable, False)
        oDlg.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
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
        fOut = StringIO.StringIO()
        oWriter.write(fOut, CardSetWrapper(oCardSet))
        oTextBuffer.set_text(fOut.getvalue())
        fOut.close()


class ExportBuffer(gtk.TextBuffer):
    # pylint: disable=R0904
    # gtk.Widget, so many public methods
    """Buffer object for showing the exported card set text"""

    def __init__(self):
        super(ExportBuffer, self).__init__(None)
        self.create_tag("text", left_margin=0)

    def set_text(self, sCardSetText):
        """Set the buffer contents to the card set text"""
        oStart, oEnd = self.get_bounds()
        self.delete(oStart, oEnd)
        oIter = self.get_iter_at_offset(0)
        self.insert_with_tags_by_name(oIter, sCardSetText, "text")
