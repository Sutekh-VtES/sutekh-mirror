# ImportDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Dialog for handling File Import Events"""

import gtk
from sutekh.gui.SutekhFileWidget import SutekhFileDialog

class ImportDialog(SutekhFileDialog):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Prompt the user for a file name to import"""
    def __init__(self, sTitle, oParent):
        super(ImportDialog, self).__init__(oParent, sTitle,
                gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.button_response)
        self.set_local_only(True)
        self.set_select_multiple(False)
        self.sName = None

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """Handle the button press event."""
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.get_filename()
        self.destroy()

    def get_name(self):
        """Return the name to the caller."""
        return self.sName
