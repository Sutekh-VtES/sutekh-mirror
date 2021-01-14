# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog with progress meter
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""classes needed for the progress dialog"""

# pylint: disable=deprecated-module
# we need data from the string module
import string
# pylint: enable=deprecated-module
from logging import Handler

from gi.repository import Gdk, Gtk


PROGRESS_CSS = b'''
    trough {
        min-height: 20px;
    }
    progress {
        min-height: 18px;
    }
'''


class SutekhLogHandler(Handler):
    """Base class for loggers to talk to the dialog"""
    # We explicitly inherit from object, since Handler is a classic class
    def __init__(self):
        super().__init__()
        self.oDialog = None

    def set_dialog(self, oDialog):
        """point to the progress dialog"""
        self.oDialog = oDialog

    def emit(self, _oRecord):
        """Default emit handler"""


class SutekhHTMLLogHandler(SutekhLogHandler):
    """Logging class for cardlist and rulings parser.

       Converts messages of the form 'Card: X' into an approximate
       progress measure
       """
    # Massage messages from HTMLParser into Dialog updates
    def emit(self, oRecord):
        """Massage message into progress value.

           Skip difficult cases (The X, non-ascii characters, etc.)
           """
        if self.oDialog is None:
            return  # No point
        sString = oRecord.getMessage()
        # We skip considering the 'The' cases, as that gets messy
        if sString.startswith('Card: The '):
            return
        sBase = sString[6:8]
        sStart = sBase.upper()
        # The cardlist considers case in ordering - AK before Aabat, etc.
        # This causes jumps, so we ignore these, as there aren't enough
        # to make this worthwhile (9 out 3009, Jan 2008 - NM)
        if sStart == sBase:
            return
        # Skip the difficult, non-ascii encoding cases
        if sStart[0] not in string.ascii_uppercase or \
                sStart[1] not in string.ascii_uppercase:
            return
        # This is now safe, if not a particularly good idea
        iPos = ord(sStart[0]) * 26 + ord(sStart[1]) - (ord('A') * 27)
        fBarPos = iPos / float(26 * 26)
        self.oDialog.update_bar(fBarPos)


class SutekhCountLogHandler(SutekhLogHandler):
    """LogHandler class for dealing with database upgrade messages.

       Each message (Card List, card set, etc). is taken as a step in the
       process.
       """
    def __init__(self):
        super().__init__()
        self.iCount = None
        self.fTot = None

    def set_total(self, iTot):
        """Set the total number of steps."""
        self.fTot = float(iTot)
        self.iCount = 0

    def emit(self, _oRecord):
        """Handle a emitted signal, updating the progress count."""
        if self.oDialog is None:
            return  # No point
        self.iCount += 1
        fBarPos = self.iCount / self.fTot
        self.oDialog.update_bar(fBarPos)


class ProgressDialog(Gtk.Window):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Show a window with a single progress bar."""
    # This is not a proper dialog, since we don't want the blocking
    # behaviour of Dialog.run()
    def __init__(self):
        super().__init__()
        self.set_title('Progress')
        self.set_name('Sutekh.dialog')
        self.oProgressBar = Gtk.ProgressBar()
        self.oProgressBar.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.oProgressBar.set_inverted(False)
        self.oProgressBar.set_text('% done')
        self.oProgressBar.set_fraction(0.0)
        self.oProgressBar.set_size_request(350, 50)
        self.oProgressBar.set_show_text(True)
        oProvider = Gtk.CssProvider()
        oProvider.load_from_data(PROGRESS_CSS)
        oContext = self.oProgressBar.get_style_context()
        oContext.add_provider(oProvider,
                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.set_default_size(400, 100)
        self.oVBox = Gtk.VBox()
        self.oDescription = Gtk.Label('Unknown')
        self.oVBox.pack_start(self.oDescription, False, True, 0)
        # Centre the progress bar horizontally
        oAlign = Gtk.Alignment(xalign=0.5, yalign=0.0)
        oAlign.add(self.oProgressBar)
        self.oVBox.pack_end(oAlign, False, True, 0)
        self.add(self.oVBox)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.show_all()
        self.set_modal(True)

    def set_description(self, sDescription):
        """Change the description of a dialog"""
        self.oVBox.remove(self.oDescription)
        self.oDescription = Gtk.Label(sDescription)
        self.oVBox.pack_start(self.oDescription, False, True, 0)
        self.show_all()

    def reset(self):
        """Reset the progress bar to zero"""
        self.update_bar(0.0)

    def set_complete(self):
        """Set the progress bar as being complete."""
        self.update_bar(1.0)

    def update_bar(self, fStep):
        """Update the progress bar to the given fStep value."""
        # Progress bar doesn't like values < 0.0 or > 1.0
        if fStep > 1.0:
            self.oProgressBar.set_fraction(1.0)
            self.oProgressBar.set_text('100% complete')
        elif fStep < 0.0:
            self.oProgressBar.set_fraction(0.0)
            self.oProgressBar.set_text(' 0% complete')
        else:
            self.oProgressBar.set_fraction(fStep)
            self.oProgressBar.set_text('%2.0f%% complete' % (fStep * 100))
        # Since Sutekh is single threaded, and some IO bound
        # task has the Gtk.main loop process, we fudge the
        # required behaviour to get the update drawn
        while Gtk.events_pending():
            Gtk.main_iteration()
