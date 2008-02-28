# ImportDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Dialog for handling File Import Events"""

import gtk

class ImportDialog(gtk.FileChooserDialog):
    def __init__(self, sTitle, oParent):
        super(ImportDialog, self).__init__(sTitle, oParent,
                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.buttonResponse)
        self.set_local_only(True)
        self.set_select_multiple(False)
        self.sName = None

    def buttonResponse(self, oWidget, iResponse):
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.get_filename()
        self.destroy()

    def getName(self):
        return self.sName
