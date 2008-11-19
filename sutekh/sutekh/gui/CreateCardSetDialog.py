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
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet

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
        self.oName = gtk.Entry(50)
        oAuthorLabel = gtk.Label("Author : ")
        self.oAuthor = gtk.Entry(50)
        oCommentriptionLabel = gtk.Label("Description : ")
        self.oComment = gtk.Entry()
        oParentLabel = gtk.Label("This card set is a subset of : ")
        self.oParentList = gtk.combo_box_new_text()
        if not oCardSetParent and oCardSet:
            oCardSetParent = oCardSet.parent
        # pylint: disable-msg=E1101
        # vbox, sqlobject confuse pylint
        self.oParentList.append_text('No Parent')
        if not oCardSetParent:
            # Select this when no parent is specified
            self.oParentList.set_active(0)
        for iNum, oLoopCardSet in enumerate(
                PhysicalCardSet.select().orderBy('name')):
            self.oParentList.append_text(oLoopCardSet.name)
            if oCardSetParent and oCardSetParent.name == oLoopCardSet.name:
                self.oParentList.set_active(iNum + 1)
        oAnnotateLabel = gtk.Label("Annotations : ")
        oTextView = gtk.TextView()
        self.oBuffer = oTextView.get_buffer()

        self.vbox.pack_start(oNameLabel, expand=False)
        self.vbox.pack_start(self.oName, expand=False)
        self.vbox.pack_start(oAuthorLabel, expand=False)
        self.vbox.pack_start(self.oAuthor, expand=False)
        self.vbox.pack_start(oCommentriptionLabel, expand=False)
        self.vbox.pack_start(self.oComment, expand=False)
        self.vbox.pack_start(oParentLabel, expand=False)
        self.vbox.pack_start(self.oParentList, expand=False)
        self.vbox.pack_start(oAnnotateLabel, expand=False)
        oScrolledWin = AutoScrolledWindow(oTextView)
        self.set_default_size(500, 500)
        self.vbox.pack_start(oScrolledWin, expand=True)

        self.connect("response", self.button_response)

        self.sOrigName = sName
        if sName is not None:
            self.oName.set_text(sName)

        if oCardSet is not None:
            if not sName:
                self.oName.set_text(oCardSet.name)
                self.sOrigName = oCardSet.name
            self.oAuthor.set_text(oCardSet.author)
            self.oComment.set_text(oCardSet.comment)
            if oCardSet.annotations:
                self.oBuffer.set_text(oCardSet.annotations)

        self.sName = None
        self.oParent = oCardSetParent

        self.show_all()

    def get_name(self):
        """Get the name entred by the user"""
        return self.sName

    def get_author(self):
        """Get the author value"""
        return self.oAuthor.get_text()

    def get_comment(self):
        """Get the comment value"""
        return self.oComment.get_text()

    def get_annotations(self):
        """Get the comment value"""
        sAnnotations = self.oBuffer.get_text(
                self.oBuffer.get_start_iter(), self.oBuffer.get_end_iter())
        return sAnnotations

    def get_parent(self):
        """Get the chosen parent card set, or None if 'No Parent' is chosen"""
        return self.oParent

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """Handle button press from the dialog."""
        if iResponse == gtk.RESPONSE_OK:
            self.sName = self.oName.get_text()
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
                if self.oParentList.get_active() > 0:
                    # Get the parent object for this card set
                    sParent = self.oParentList.get_active_text()
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
