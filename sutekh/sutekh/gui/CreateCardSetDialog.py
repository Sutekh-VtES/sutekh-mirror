# CreateCardSetDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog to create a new PhysicalCardSet or AbstrctCardSet
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Get details for a new card set"""

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error

class CreateCardSetDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Prompt the user for the name of a new card set.

       Optionally, get Author + Description.
       """
    def __init__(self, oParent, sType, sAuthor=None, sDesc=None):
        super(CreateCardSetDialog, self).__init__(sType + " Card Set Details",
            oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oNameLabel = gtk.Label("Card Set Name : ")
        self.oName = gtk.Entry(50)
        oAuthorLabel = gtk.Label("Author : ")
        self.oAuthor = gtk.Entry(50)
        oDescriptionLabel = gtk.Label("Description : ")
        self.oDesc = gtk.Entry(50)

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.vbox.pack_start(oNameLabel)
        self.vbox.pack_start(self.oName)
        self.vbox.pack_start(oAuthorLabel)
        self.vbox.pack_start(self.oAuthor)
        self.vbox.pack_start(oDescriptionLabel)
        self.vbox.pack_start(self.oDesc)

        self.connect("response", self.button_response)

        if sAuthor is not None:
            self.oAuthor.set_text(sAuthor)

        if sDesc is not None:
            self.oDesc.set_text(sDesc)

        self.sName = None
        self.sAuthor = None
        self.sDesc = None
        self.sType = sType

        self.show_all()

    def get_data(self):
        """Return data about the new card set to the caller."""
        return (self.sName, self.sAuthor, self.sDesc)

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """Handle button press from the dialog."""
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.oName.get_text()
            if len(self.sName) > 0:
                self.sAuthor = self.oAuthor.get_text()
                self.sDesc = self.oDesc.get_text()
                # We don't allow < or > in the name, since
                # pygtk uses that for markup
                self.sName = self.sName.replace("<", "(")
                self.sName = self.sName.replace(">", ")")
            else:
                # We don't allow empty names
                self.sName = None
                do_complaint_error("You did not specify a name for the"
                        " %s Card Set." % self.sType)
        self.destroy()
