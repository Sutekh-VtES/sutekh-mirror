# AboutDialog.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhInfo import SutekhInfo

class SutekhAboutDialog(gtk.AboutDialog):
    """About dialog for Sutekh."""

    def __init__(self,*args,**kwargs):
        super(SutekhAboutDialog,self).__init__(*args,**kwargs)

        self.set_name(SutekhInfo.NAME)
        self.set_version(SutekhInfo.VERSION_STR)
        self.set_copyright(SutekhInfo.LICENSE)
        self.set_comments(SutekhInfo.DESCRIPTION)
        self.set_license(SutekhInfo.LICENSE_TEXT)
        self.set_wrap_license(False) # don't automatically wrap license text
        self.set_website(SutekhInfo.SOURCEFORGE_URL)
        # self.set_website_label(website_label)
        self.set_authors([tAuth[0] for tAuth in SutekhInfo.AUTHORS])
        # self.set_documenters(documenters)
        # self.set_artists(artists)
        # self.set_translator_credits(translator_credits)
        # self.set_logo(logo)
        # self.set_logo_icon_name(icon_name)
