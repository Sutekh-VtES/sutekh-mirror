# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Simple about dialog for Sutekh"""

from gi.repository import Gtk

from sutekh.base.Utility import get_database_url

from sutekh.gui import SutekhIcon
from sutekh.SutekhInfo import SutekhInfo


class SutekhAboutDialog(Gtk.AboutDialog):
    """About dialog for Sutekh."""
    # pylint: disable=too-many-public-methods
    # Gtk Widget, so has many public methods

    def __init__(self, *aArgs, **kwargs):
        super().__init__(*aArgs, **kwargs)

        self.set_name(SutekhInfo.NAME)
        self.set_version(SutekhInfo.VERSION_STR)
        self.set_copyright(SutekhInfo.LICENSE)
        self.set_comments(SutekhInfo.DESCRIPTION)
        self.set_license(SutekhInfo.LICENSE_TEXT)
        self.set_wrap_license(False)  # don't automatically wrap license text
        self.set_website(SutekhInfo.SOURCEFORGE_URL)
        self.set_website_label("Website")
        self.set_authors([tAuth[0] for tAuth in SutekhInfo.AUTHORS])
        self.set_documenters([tAuth[0] for tAuth in SutekhInfo.DOCUMENTERS])
        self.set_artists([tAuth[0] for tAuth in SutekhInfo.ARTISTS])
        self.set_logo(SutekhIcon.SUTEKH_ICON)
        # self.set_translator_credits(translator_credits)
        # pylint: disable=no-member
        # pylint doesn't like the dialog vbox
        oUrlText = Gtk.Label('Database URI: %s' % get_database_url())
        self.vbox.pack_end(oUrlText, False, False, 0)
        oUrlText.show()
