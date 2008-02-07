# SutekhDialog.py
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Provides base class for the dailogs used in Sutekh - ensures set_name
# is called consistently
# Also provides helpful wrapper functions around gtk.MessageDialog's

import gtk

class SutekhDialog(gtk.Dialog):
    """
    wrapper class for gtk.Dialog
    """
    def __init__(self, sTitle, oParent=None, iFlags=0, oButtons=None):
        super(SutekhDialog, self).__init__(sTitle, oParent, iFlags, oButtons)
        self.set_name("Sutekh.dialog")

def do_complaint(sMessage, oDialogType, oButtonType, bMarkup=False):
    """
    Wrapper function for gtk.MessageDialog.
    Create the dialog, run it, and return the result
    if bMarkup is true, the string is interpreted as markup,
    other, just as plain text
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
    """
    Wrapper function for gtk.MessageDialog, using add_button to create
    custom button layouts.
    Create the dialog, run it, and return the result
    if bMarkup is true, the string is interpreted as markup,
    other, just as plain text
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
    return do_complaint(sMessage, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, False)

def do_complaint_warning(sMessage):
    return do_complaint(sMessage, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, False)
