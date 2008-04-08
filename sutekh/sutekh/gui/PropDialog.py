# PropDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for handling Card Set Properties
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Dialog for editing basic card set properties"""

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog

class PropDialog(SutekhDialog):
    """Dialog for editing basic propeties.

       Allow the user to edit/set the card set name, the author and
       the description field.
       """
    # pylint: disable-msg=R0904
    # gtk class, so many pulic methods
    def __init__(self, sTitle, oParent, sCurName, sCurAuthor, sCurComment):
        super(PropDialog, self).__init__(sTitle, oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.button_response)
        oNameLabel = gtk.Label("Card Set Name : ")
        oAuthLabel = gtk.Label("Author : ")
        oCommLabel = gtk.Label("Description : ")
        self.oName = gtk.Entry(50)
        self.oAuthor = gtk.Entry(50)
        self.oComment = gtk.Entry()
        self.oName.set_text(sCurName)
        self.oAuthor.set_text(sCurAuthor)
        self.oComment.set_text(sCurComment)
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.vbox.pack_start(oNameLabel)
        self.vbox.pack_start(self.oName)
        self.vbox.pack_start(oAuthLabel)
        self.vbox.pack_start(self.oAuthor)
        self.vbox.pack_start(oCommLabel)
        self.vbox.pack_start(self.oComment)
        self.show_all()
        self.sName = None
        self.sAuthor = None
        self.sComment = None

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """Handle the dialog response signal."""
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.oName.get_text()
            self.sAuthor = self.oAuthor.get_text()
            self.sComment = self.oComment.get_text()
        self.destroy()

    def get_data(self):
        """Return the data entered by the user."""
        return (self.sName, self.sAuthor, self.sComment)
