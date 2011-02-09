# SutekhDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Provides base class for the dailogs used in Sutekh - ensures set_name
# is called consistently
# Also provides helpful wrapper functions around gtk.MessageDialog's

"""Dialog wrapper and functions for Sutekh"""

import gtk
import logging
import sys
import traceback
from gobject import markup_escape_text


class SutekhDialog(gtk.Dialog):
    # pylint: disable-msg=R0904
    # gtk widget, so has many public methods
    """wrapper class for gtk.Dialog"""
    def __init__(self, sTitle, oParent=None, iFlags=0, oButtons=None):
        super(SutekhDialog, self).__init__(sTitle, oParent, iFlags, oButtons)
        self.set_name("Sutekh.dialog")


def do_complaint(sMessage, oDialogType, oButtonType, bMarkup=False):
    """Wrapper function for gtk.MessageDialog.

       Create the dialog, run it, and return the result. If bMarkup is true,
       the string is interpreted as markup, other, just as plain text
       """
    if bMarkup:
        oComplaint = gtk.MessageDialog(None, 0, oDialogType,
                oButtonType, None)
        oComplaint.set_markup(sMessage)
    else:
        oComplaint = gtk.MessageDialog(None, 0, oDialogType,
                oButtonType, sMessage)
    oComplaint.set_name("Sutekh.dialog")
    iResponse = oComplaint.run()
    oComplaint.destroy()
    return iResponse


def do_complaint_buttons(sMessage, oType, aButtonInfo, bMarkup=False):
    """Wrapper function for gtk.MessageDialog, using add_button to create
       custom button layouts.

       Create the dialog, run it, and return the result. If bMarkup is true,
       the string is interpreted as markup, other, just as plain text.
       """
    if bMarkup:
        oComplaint = gtk.MessageDialog(None, 0, oType,
                gtk.BUTTONS_NONE, None)
        oComplaint.set_markup(sMessage)
    else:
        oComplaint = gtk.MessageDialog(None, 0, oType,
                gtk.BUTTONS_NONE, sMessage)
    for oItem, oResponse in zip(aButtonInfo[0::2], aButtonInfo[1::2]):
        oComplaint.add_button(oItem, oResponse)
    oComplaint.set_name("Sutekh.dialog")
    iResponse = oComplaint.run()
    oComplaint.destroy()
    return iResponse


def do_complaint_error(sMessage):
    """Error dialog with close button"""
    return do_complaint(sMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, False)


def do_complaint_warning(sMessage):
    """Warning dialog with OK and CANCEL buttons"""
    return do_complaint(sMessage, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL,
            False)


class DetailDialog(SutekhDialog):
    """Message dialog with a details expander"""
    # pylint: disable-msg=R0904
    # gtk widget, so has many public methods

    def __init__(self, sMessage, sDetails):
        super(DetailDialog, self).__init__('Sutekh has encounterd an error',
                oButtons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        oHBox = gtk.HBox(False, 2)
        oMessageBox = gtk.VBox(False, 2)
        oImage = gtk.Image()
        oImage.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
        oImage.set_alignment(0, 0)
        oHBox.pack_start(oImage, expand=False)
        oInfo = gtk.Label()
        oInfo.set_markup('<b>%s</b>' % markup_escape_text(sMessage))
        oInfo.set_alignment(0, 0)
        oInfo.set_selectable(True)
        oMessageBox.pack_start(oInfo, expand=False)
        oExpander = gtk.Expander('Details')
        oFrame = gtk.Frame()
        oDetails = gtk.Label(sDetails)
        oDetails.set_selectable(True)
        oFrame.add(oDetails)
        oExpander.add(oFrame)
        oMessageBox.pack_start(oExpander)
        oHBox.pack_start(oMessageBox)
        self.vbox.pack_start(oHBox)
        oExpander.set_expanded(False)
        self.show_all()
        self.set_name("Sutekh.dialog")


def do_complaint_error_details(sMessage, sDetails):
    """Popup an details dialog for an error"""
    oComplaint = DetailDialog(sMessage, sDetails)
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
