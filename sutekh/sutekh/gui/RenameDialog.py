# RenameDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007, 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# (Extracted from CardSetImport.py)
# GPL - see COPYING for details

"""Dialog to handle the Rename / Replace / Cancel options when importing
   a card set with a name that's already in use."""

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.core.SutekhObjects import PhysicalCardSet, MAX_ID_LENGTH

RENAME, REPLACE, PROMPT = 1, 2, 3


class RenameDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # gtk widget, so has many public methods
    """Class to handle the card set renaming"""

    def __init__(self, sOldName):
        # Do this first, so we get the buttons right
        self.oEntry = gtk.Entry(MAX_ID_LENGTH)
        if sOldName:
            sMsg = "Card Set %s already exists.\n" \
                    "Please choose a new name or choose to replace the" \
                    " card set.\n" \
                    "Choose cancel to abort this import." % sOldName
            tButtons = ('Rename card set', RENAME, 'Replace Existing Card Set',
                    REPLACE, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            self.oEntry.set_text(sOldName)
        else:
            sMsg = "No name given for the card set\n" \
                    "Please specify a name.\n" \
                    "Choose cancel to abort this import."
            tButtons = ('Name card set', RENAME, gtk.STOCK_CANCEL,
                    gtk.RESPONSE_CANCEL)
        super(RenameDialog, self).__init__("Choose New Card Set Name",
                None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                tButtons)
        oLabel = gtk.Label(sMsg)
        self.sNewName = ""

        # Need this so entry box works as expected
        self.oEntry.connect("activate", self.handle_response, RENAME)
        self.connect("response", self.handle_response)

        # pylint: disable-msg=E1101
        # pylint misses vbox methods
        self.vbox.pack_start(oLabel)
        self.vbox.pack_start(self.oEntry)
        self.show_all()

    def handle_response(self, _oWidget, oResponse):
        """Handle the user's clicking on OK or CANCEL in the dialog."""
        if oResponse == RENAME:
            # Check the name
            sNewName = self.oEntry.get_text().strip()
            if not sNewName:
                do_complaint_error("No name specified.\n"
                        "Please choose a suitable name")
                return self.run()  # Reprompt
            elif PhysicalCardSet.selectBy(name=sNewName).count() != 0:
                # FIXME: do we want to allow the user to force a replace here?
                do_complaint_error("The name %s is in use.\n"
                        "Please choose a different name" % sNewName)
                return self.run()  # Reprompt
            else:
                self.sNewName = sNewName
