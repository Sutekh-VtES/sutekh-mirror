# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Database to prompt for datapack updates and so forth."""

from gi.repository import Gtk

from .SutekhDialog import SutekhDialog


class UpdateDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Dialog which prompts the user if datapack or other updates
       are available."""
    def __init__(self, aMessages):
        # Create Dialog
        super().__init__("Updates available", None, Gtk.DialogFlags.MODAL,
                         ("_Cancel", Gtk.ResponseType.CANCEL,
                          "_OK", Gtk.ResponseType.OK))
        oHBox = Gtk.HBox(False, 0)
        oIcon = Gtk.Image.new_from_icon_name('dialog-information',
                                             Gtk.IconSize.DIALOG)
        oHBox.pack_start(oIcon, True, True, 0)
        self.vbox.pack_start(oHBox, True, True, 0)
        sLabel = "Updates are available. Download now?"
        oLabel = Gtk.Label(sLabel)
        oHBox.pack_start(oLabel, True, True, 0)
        sLabelInfo = "The following updates are available:\n\n"
        sLabelInfo += "\n".join(aMessages)
        oInfolabel = Gtk.Label()
        oInfolabel.set_markup(sLabelInfo)
        self.vbox.pack_start(oInfolabel, True, True, 0)
        self.set_default_response(Gtk.ResponseType.OK)
        self.show_all()
