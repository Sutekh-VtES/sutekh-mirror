# ExportDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Dialog for handling File Export Events"""

import gtk

class ExportDialog(gtk.FileChooserDialog):
    def __init__(self, sTitle, oParent):
        super(ExportDialog, self).__init__(sTitle, oParent,
                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.buttonResponse)
        self.set_local_only(True)
        self.set_do_overwrite_confirmation(True)
        self.sName = None

    def buttonResponse(self, oWidget, iResponse):
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.get_filename()
        self.destroy()

    def getName(self):
        return self.sName
