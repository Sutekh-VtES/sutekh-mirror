# ShowExportedCardSet.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for displaying the exported version of a card set in a gtk.TextView.
   Intended to make cutting and pasting easier."""

import gtk
import StringIO
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.io.WriteJOL import WriteJOL
from sutekh.io.WriteLackeyCCG import WriteLackeyCCG
from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.io.WriteVEKNForum import WriteVEKNForum
from sutekh.io.WriteCSV import WriteCSV


class ShowExported(SutekhPlugin):
    """Display the various exported versions of a card set.

       The card set is shown in a textview, and the user can toggle between
       the different formats. This is designed to make it trivial to
       cut-n-paste the card set into something else (such as a web-browser).
       """

    dTableVersions = {}
    aModelsSupported = (PhysicalCardSet,)

    _dExporters = {
            # radio button text : Writer
            'Export to JOL format': WriteJOL,
            'Export to Lackey CCG format': WriteLackeyCCG,
            'Export to ARDB Text': WriteArdbText,
            'BBcode output for the V:EKN Forums': WriteVEKNForum,
            'Export to ELDB ELD Deck File': WriteELDBDeckFile,
            'CSV Export (with headers)': WriteCSV,
            }

    def get_menu_item(self):
        """Register on the 'Analyze' menu"""
        if not self.check_versions() or not self.check_model_type():
            return None
        oShowExported = gtk.MenuItem("Display card set in alternative format")
        oShowExported.connect("activate", self.activate)
        return ('Actions', oShowExported)

    def activate(self, _oWidget):
        """Handle response from menu"""
        oCardSet = self.get_card_set()
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
        oDlg.vbox.pack_start(AutoScrolledWindow(oTextView))
        # Add the radio buttons
        oTable = gtk.Table(len(self._dExporters) / 2, 2)
        oIter = self._dExporters.iterkeys()
        iXPos, iYPos = 0, 0
        oFirstBut = None
        for sName in oIter:
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
        cWriter = self._dExporters[sName]
        oWriter = cWriter()
        fOut = StringIO.StringIO()
        oWriter.write(fOut, CardSetWrapper(oCardSet))
        oTextBuffer.set_text(fOut.getvalue())
        fOut.close()


class ExportBuffer(gtk.TextBuffer):
    # pylint: disable-msg=R0904
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


plugin = ShowExported
