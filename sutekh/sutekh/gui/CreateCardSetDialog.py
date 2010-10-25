# CreateCardSetDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog to create a new PhysicalCardSet or AbstrctCardSet
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Get details for a new card set"""

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.CardSetsListView import CardSetsListView
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.core.SutekhObjects import IPhysicalCardSet, MAX_ID_LENGTH


def make_scrolled_text(oCardSet, sAttr):
    """Create a text buffer wrapped in a scrolled window, filled with
       the contents of sAtter if available"""

    oTextView = gtk.TextView()
    oBuffer = oTextView.get_buffer()
    oScrolledWin = AutoScrolledWindow(oTextView)
    if oCardSet:
        # Check for None values
        sValue = getattr(oCardSet, sAttr)
        if sValue:
            oBuffer.set_text(sValue)
    return oBuffer, oScrolledWin


class CreateCardSetDialog(SutekhDialog):
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - We manage a bunch of state, so need several attributes
    """Prompt the user for the name of a new card set.

       Optionally, get Author + Description.
       """
    def __init__(self, oParent, sName=None, oCardSet=None,
            oCardSetParent=None):
        super(CreateCardSetDialog, self).__init__("Card Set Details",
            oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        oNameLabel = gtk.Label("Card Set Name : ")
        self.oName = gtk.Entry(MAX_ID_LENGTH)
        oAuthorLabel = gtk.Label("Author : ")
        self.oAuthor = gtk.Entry()
        oCommentriptionLabel = gtk.Label("Description : ")
        self.oCommentBuffer, oCommentWin = make_scrolled_text(oCardSet,
                'comment')
        oParentLabel = gtk.Label("This card set is a subset of : ")
        self.oParentList = CardSetsListView(None, self)
        self.oParentList.set_size_request(100, 200)
        oAnnotateLabel = gtk.Label("Annotations : ")
        self.oAnnotateBuffer, oAnnotateWin = make_scrolled_text(oCardSet,
                'annotations')

        self.oInUse = gtk.CheckButton('Mark card Set as In Use')

        self.set_default_size(500, 500)
        # pylint: disable-msg=E1101
        # gtk methods confuse pylint
        self.vbox.pack_start(oNameLabel, expand=False)
        self.vbox.pack_start(self.oName, expand=False)
        self.vbox.pack_start(oAuthorLabel, expand=False)
        self.vbox.pack_start(self.oAuthor, expand=False)
        self.vbox.pack_start(oCommentriptionLabel, expand=False)
        self.vbox.pack_start(oCommentWin, expand=True)
        self.vbox.pack_start(oParentLabel, expand=False)
        self.vbox.pack_start(AutoScrolledWindow(self.oParentList), expand=True)
        self.vbox.pack_start(oAnnotateLabel, expand=False)
        self.vbox.pack_start(oAnnotateWin, expand=True)
        self.vbox.pack_start(self.oInUse, expand=False)

        self.connect("response", self.button_response)

        self.sOrigName = sName
        if sName is not None:
            self.oName.set_text(sName)

        if oCardSet is not None:
            if not sName:
                self.oName.set_text(oCardSet.name)
                self.sOrigName = oCardSet.name
                self.oParentList.exclude_set(self.sOrigName)
            if oCardSetParent is None and oCardSet.parent is not None:
                self.oParentList.set_selected_card_set(oCardSet.parent.name)
            if oCardSet.author is not None:
                self.oAuthor.set_text(oCardSet.author)
            self.oInUse.set_active(oCardSet.inuse)

        self.sName = None
        self.sAuthor = None
        self.oParent = oCardSetParent

        self.show_all()

    def get_name(self):
        """Get the name entered by the user"""
        return self.sName

    def get_author(self):
        """Get the author value"""
        return self.sAuthor

    def get_comment(self):
        """Get the comment value"""
        sComment = self.oCommentBuffer.get_text(
                self.oCommentBuffer.get_start_iter(),
                self.oCommentBuffer.get_end_iter())
        return sComment

    def get_annotations(self):
        """Get the comment value"""
        sAnnotations = self.oAnnotateBuffer.get_text(
                self.oAnnotateBuffer.get_start_iter(),
                self.oAnnotateBuffer.get_end_iter())
        return sAnnotations

    def get_parent(self):
        """Get the chosen parent card set, or None if 'No Parent' is chosen"""
        return self.oParent

    def get_in_use(self):
        """Get the In Use checkbox status"""
        return self.oInUse.get_active()

    def button_response(self, _oWidget, iResponse):
        """Handle button press from the dialog."""
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.oName.get_text()
            self.sAuthor = self.oAuthor.get_text()
            if len(self.sName) > 0:
                # We don't allow < or > in the name, since pango uses that for
                # markup
                self.sName = self.sName.replace("<", "(")
                self.sName = self.sName.replace(">", ")")
                if self.sName != self.sOrigName:
                    # check if card set exists
                    # pylint: disable-msg=W0704
                    # doing nothing is correct here
                    try:
                        IPhysicalCardSet(self.sName)
                        do_complaint_error('Chosen Card Set Name is'
                                ' already in use')
                        self.sName = None
                        self.destroy()
                        return
                    except SQLObjectNotFound:
                        pass
                sParent = self.oParentList.get_selected_card_set()
                if sParent:
                    # Get the parent object for this card set
                    self.oParent = IPhysicalCardSet(sParent)
                else:
                    # 'No parent' option selected, so use none
                    self.oParent = None
            else:
                # We don't allow empty names
                self.sName = None
                do_complaint_error("You did not specify a name for the"
                        " Card Set.")
        self.destroy()
