# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Provides base class for the dailogs used in Sutekh - ensures set_name
# is called consistently
# Also provides helpful wrapper functions around Gtk.MessageDialog's

"""Dialog wrapper and functions for Sutekh"""

import logging
import sys
import traceback

from gi.repository import Gtk, GLib

from sutekh.SutekhInfo import SutekhInfo as AppInfo

from ..Utility import get_database_url


class SutekhDialog(Gtk.Dialog):
    # pylint: disable=too-many-public-methods
    # Gtk widget, so has many public methods
    """wrapper class for Gtk.Dialog"""
    def __init__(self, sTitle, oParent=None, iFlags=0, oButtons=None):
        super().__init__(sTitle, oParent, iFlags, oButtons)
        self.set_name("Sutekh.dialog")


def do_complaint(sMessage, oDialogType, oButtonType, bMarkup=False):
    """Wrapper function for Gtk.MessageDialog.

       Create the dialog, run it, and return the result. If bMarkup is true,
       the string is interpreted as markup, other, just as plain text
       """
    if bMarkup:
        oComplaint = Gtk.MessageDialog(None, 0, oDialogType,
                                       oButtonType, None)
        oComplaint.set_markup(sMessage)
    else:
        oComplaint = Gtk.MessageDialog(None, 0, oDialogType,
                                       oButtonType, sMessage)
    oComplaint.set_name("Sutekh.dialog")
    iResponse = oComplaint.run()
    oComplaint.destroy()
    return iResponse


def do_complaint_buttons(sMessage, oType, aButtonInfo, bMarkup=False):
    """Wrapper function for Gtk.MessageDialog, using add_button to create
       custom button layouts.

       Create the dialog, run it, and return the result. If bMarkup is true,
       the string is interpreted as markup, other, just as plain text.
       """
    if bMarkup:
        oComplaint = Gtk.MessageDialog(None, 0, oType,
                                       Gtk.ButtonsType.NONE, None)
        oComplaint.set_markup(sMessage)
    else:
        oComplaint = Gtk.MessageDialog(None, 0, oType,
                                       Gtk.ButtonsType.NONE, sMessage)
    for oItem, oResponse in zip(aButtonInfo[0::2], aButtonInfo[1::2]):
        oComplaint.add_button(oItem, oResponse)
    oComplaint.set_name("Sutekh.dialog")
    iResponse = oComplaint.run()
    oComplaint.destroy()
    return iResponse


def do_complaint_error(sMessage):
    """Error dialog with close button"""
    return do_complaint(sMessage, Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.CLOSE, False)


def do_complaint_warning(sMessage):
    """Warning dialog with OK and CANCEL buttons"""
    return do_complaint(sMessage, Gtk.MessageType.WARNING,
                        Gtk.ButtonsType.OK_CANCEL, False)


def do_info_message(sMessage, bMarkup=True):
    """Info dialog with a close button.

       We default to markup enabled as that's generally useful in this case
       and we're usually not including tracebacks or other text that will
       break the markup parser."""
    return do_complaint(sMessage, Gtk.MessageType.INFO,
                        Gtk.ButtonsType.CLOSE, bMarkup)


class DetailDialog(SutekhDialog):
    """Message dialog with a details expander"""
    # pylint: disable=too-many-public-methods
    # Gtk widget, so has many public methods

    def __init__(self, sMessage, sDetails):
        super().__init__(
            '%s has encounterd an error' % AppInfo.NAME,
            oButtons=("_Close", Gtk.ResponseType.CLOSE))
        oHBox = Gtk.HBox(False, 2)
        oMessageBox = Gtk.VBox(homogeneous=False, spacing=2)
        oImage = Gtk.Image.new_from_icon_name('dialog-error',
                                              Gtk.IconSize.DIALOG)
        oImage.set_alignment(0, 0)
        oHBox.pack_start(oImage, False, True, 0)
        oInfo = Gtk.Label()
        oInfo.set_markup('<b>%s</b>' % GLib.markup_escape_text(sMessage))
        oInfo.set_alignment(0, 0)
        oInfo.set_selectable(True)
        oMessageBox.pack_start(oInfo, False, True, 0)
        oExpander = Gtk.Expander()
        oExpander.set_label('Details')
        oFrame = Gtk.Frame()
        oDetails = Gtk.Label(sDetails)
        oDetails.set_selectable(True)
        oFrame.add(oDetails)
        oExpander.add(oFrame)
        oMessageBox.pack_start(oExpander, True, True, 0)
        oHBox.pack_start(oMessageBox, True, True, 0)
        self.vbox.pack_start(oHBox, True, True, 0)
        oExpander.set_expanded(False)
        self.show_all()
        self.set_name("Sutekh.dialog")


def format_app_info():
    """Format the application details nicely for the error dialogs."""
    return "%s version %s\nDatabase: %s\n\n" % (AppInfo.NAME,
                                                AppInfo.VERSION_STR,
                                                get_database_url())


def do_complaint_error_details(sMessage, sDetails):
    """Popup an details dialog for an error"""
    oComplaint = DetailDialog(sMessage, '\n'.join([format_app_info(),
                                                   sDetails]))
    iResponse = oComplaint.run()
    oComplaint.destroy()
    return iResponse


def do_exception_complaint(sMessage):
    """Handle an exception - log the details for verbose info, and popup
       a detailed dialog with the info."""
    oType, oValue, oTraceback = sys.exc_info()
    aTraceback = traceback.format_exception(oType, oValue, oTraceback,
                                            limit=30)
    logging.error("%s:\n%s", sMessage, "".join(aTraceback))
    do_complaint_error_details(sMessage, "".join(aTraceback))


def exception_handler(oType, oValue, oTraceback):
    """sys.excepthook wrapper around do_complaint_error_details."""
    if oType == KeyboardInterrupt:
        # don't complain about KeyboardInterrupts
        return

    sMessage = "%s reported an unhandled exception:\n%s\n" % (AppInfo.NAME,
                                                              str(oValue))
    aTraceback = traceback.format_exception(oType, oValue, oTraceback)
    sDetails = "".join(aTraceback)

    logging.error("%s:\n%s", sMessage, '\n'.join([format_app_info(),
                                                  sDetails]))
    # We log before we show the dialog, otherwise, if there's an exception
    # while the progress bar update hack is ongoing, the error dialog won't
    # work correctly, and the exception may be lost

    do_complaint_error_details(sMessage, sDetails)


class NotebookDialog(SutekhDialog):
    """Dialog with a notebook widget."""
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods

    def __init__(self, sTitle, oParent=None, iFlags=0, oButtons=None):
        super().__init__(sTitle, oParent, iFlags, oButtons)
        self._oNotebook = Gtk.Notebook()
        self._oNotebook.set_scrollable(True)
        self._oNotebook.popup_enable()

        self.vbox.pack_start(self._oNotebook, True, True, 0)

    # pylint: disable=protected-access
    # We allow access via these properties
    notebook = property(fget=lambda self: self._oNotebook,
                        doc="Notebook Widget")
    # pylint: enable=protected-access

    def add_widget_page(self, oWidget, sTabText, sMenuText=None,
                        bMarkup=False):
        """Add a widget to the notebook as a page, specifying tab header.

           sMenuText can be used to control the text of the popup menu
           item.
           If bMarkup is True, the header text is interpreted as a markup
           string."""
        oHeader = Gtk.Label()
        if bMarkup:
            oHeader.set_markup(sTabText)
        else:
            oHeader.set_text(sTabText)
        if sMenuText:
            oMenuLabel = Gtk.Label(sMenuText)
            # Left align the menu items, to match notebook's default
            # behaviour
            oMenuLabel.set_alignment(0.0, 0.5)
            self._oNotebook.append_page_menu(oWidget, oHeader, oMenuLabel)
        else:
            self._oNotebook.append_page(oWidget, oHeader)

    def get_cur_widget(self):
        """Get the main widget of the current page."""
        iPage = self._oNotebook.get_current_page()
        return self._oNotebook.get_nth_page(iPage)

    def iter_all_page_widgets(self):
        """Iterator over all the pages in the notebook, returning
           the main widget of each page."""
        for iPage in range(self._oNotebook.get_n_pages()):
            yield self._oNotebook.get_nth_page(iPage)
