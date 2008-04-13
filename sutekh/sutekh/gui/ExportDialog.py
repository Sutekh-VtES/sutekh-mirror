# ExportDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Dialog for handling File Export Events"""

import gtk
from sutekh.gui.SutekhFileWidget import SutekhFileDialog

class ExportDialog(SutekhFileDialog):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Prompt the user for a filename to export to"""
    def __init__(self, sTitle, oParent):
        super(ExportDialog, self).__init__(oParent, sTitle,
                gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.button_response)
        self.set_local_only(True)
        self.set_do_overwrite_confirmation(True)
        self.sName = None

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """Handle button press events"""
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.get_filename()
        self.destroy()

    def get_name(self):
        """Return the name to the caller."""
        return self.sName
