# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Database to prompt for database upgrades"""

from gi.repository import Gtk
from .SutekhDialog import SutekhDialog


class DBUpgradeDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Dialog which prompts the user at the end of a database upgrade.

       Display any messages from the upgrade process, and ask the user
       whether to cancel, commit the changes, or test using the memory copy.
       """
    def __init__(self, aMessages):
        # Create Dialog
        super().__init__(
            "Memory Copy Created", None,
            Gtk.DialogFlags.MODAL, ("_Cancel", Gtk.ResponseType.CANCEL,
                                    "_OK", Gtk.ResponseType.OK))
        oHBox = Gtk.HBox(False, 0)
        oIcon = Gtk.Image.new_from_icon_name('dialog-information',
                                             Gtk.IconSize.DIALOG)
        oHBox.pack_start(oIcon, True, True, 0)
        sLabel = "Memory Copy successfully created. Commit Changes?"
        oLabel = Gtk.Label(sLabel)
        oHBox.pack_start(oLabel, True, True, 0)
        if aMessages:
            sLabelInfo = ("The following messages were reported in creating"
                          " the copy:\n")
            for sStr in aMessages:
                sLabelInfo += '<b>' + sStr + "</b>\n"
            oInfolabel = Gtk.Label()
            oInfolabel.set_markup(sLabelInfo)
            self.vbox.pack_start(oInfolabel, True, True, 0)
        self.add_button("Test upgraded database?\n"
                        "(No changes are committed)", 1)
        self.set_default_response(Gtk.ResponseType.OK)
        self.vbox.pack_start(oHBox, True, True, 0)
        self.show_all()
