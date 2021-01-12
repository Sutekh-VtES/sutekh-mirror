# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2007, 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# (Extracted from CardSetImport.py)
# GPL - see COPYING for details

"""Dialog to handle the Rename / Replace / Cancel options when importing
   a card set with a name that's already in use."""

from gi.repository import Gtk
from .SutekhDialog import SutekhDialog, do_complaint_error
from ..core.CardSetUtilities import check_cs_exists
from ..core.BaseTables import MAX_ID_LENGTH

RENAME, REPLACE, PROMPT = 1, 2, 3


class RenameDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk widget, so has many public methods
    """Class to handle the card set renaming"""

    def __init__(self, sOldName):
        # Do this first, so we get the buttons right
        self.oEntry = Gtk.Entry()
        self.oEntry.set_max_length(MAX_ID_LENGTH)
        if sOldName:
            sMsg = ("Card Set %s already exists.\n"
                    "Please choose a new name or choose to replace the"
                    " card set.\n"
                    "Choose cancel to abort this import." % sOldName)
            tButtons = ('Rename card set', RENAME, 'Replace Existing Card Set',
                        REPLACE, "_Cancel", Gtk.ResponseType.CANCEL)
            self.oEntry.set_text(sOldName)
        else:
            sMsg = ("No name given for the card set\n"
                    "Please specify a name.\n"
                    "Choose cancel to abort this import.")
            tButtons = ('Name card set', RENAME, "_Cancel",
                        Gtk.ResponseType.CANCEL)
        super().__init__("Choose New Card Set Name", None,
                         Gtk.DialogFlags.MODAL |
                         Gtk.DialogFlags.DESTROY_WITH_PARENT,
                         tButtons)
        oLabel = Gtk.Label(sMsg)
        self.sNewName = ""

        # Need this so entry box works as expected
        self.oEntry.connect("activate", self.handle_response, RENAME)
        self.connect("response", self.handle_response)

        self.vbox.pack_start(oLabel, True, True, 0)
        self.vbox.pack_start(self.oEntry, True, True, 0)
        self.show_all()

    def handle_response(self, _oWidget, oResponse):
        """Handle the user's clicking on OK or CANCEL in the dialog."""
        if oResponse == RENAME:
            # Check the name
            sNewName = self.oEntry.get_text().strip()
            if not sNewName:
                do_complaint_error("No name specified.\n"
                                   "Please choose a suitable name")
                self.run()  # Reprompt
            elif check_cs_exists(sNewName):
                do_complaint_error("The name %s is in use.\n"
                                   "Please choose a different name" % sNewName)
                # We reprompt the user, allowing them to fix things as
                # required
                self.run()
            else:
                self.sNewName = sNewName
