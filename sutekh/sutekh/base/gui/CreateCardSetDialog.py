# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog to create a new PhysicalCardSet or AbstrctCardSet
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Get details for a new card set"""

from gi.repository import Gtk
from sqlobject import SQLObjectNotFound
from .SutekhDialog import SutekhDialog, do_complaint_error
from .CardSetsListView import CardSetsListView
from .AutoScrolledWindow import AutoScrolledWindow
from .UndoTextEditor import UndoEditView
from ..core.BaseTables import MAX_ID_LENGTH
from ..core.BaseAdapters import IPhysicalCardSet


class CreateCardSetDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods
    # We manage a bunch of state, so need several attributes
    """Prompt the user for the name of a new card set.

       Optionally, get Author + Description.
       """
    def __init__(self, oParent, sName=None, oCardSet=None,
                 oCardSetParent=None):
        super().__init__(
            "Card Set Details", oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            ("_OK", Gtk.ResponseType.OK,
             "_Cancel", Gtk.ResponseType.CANCEL))

        oNameLabel = Gtk.Label(label="Card Set Name : ")
        self.oName = Gtk.Entry()
        self.oName.set_max_length(MAX_ID_LENGTH)
        oAuthorLabel = Gtk.Label(label="Author : ")
        self.oAuthor = Gtk.Entry()
        self.oCommentWin = UndoEditView('Description : ', oParent)
        if oCardSet:
            self.oCommentWin.set_text(oCardSet.comment)
        else:
            self.oCommentWin.set_text("")
        oParentLabel = Gtk.Label(label="This card set is a subset of : ")
        self.oParentList = CardSetsListView(None, self)
        self.oParentList.set_size_request(100, 200)
        self.oAnnotateWin = UndoEditView('Annotations : ', oParent)
        if oCardSet:
            self.oAnnotateWin.set_text(oCardSet.annotations)
        else:
            self.oAnnotateWin.set_text("")

        self.oInUse = Gtk.CheckButton('Mark card Set as In Use')

        self.set_default_size(800, 800)
        self.vbox.pack_start(oNameLabel, False, True, 0)
        self.vbox.pack_start(self.oName, False, True, 0)
        self.vbox.pack_start(oAuthorLabel, False, True, 0)
        self.vbox.pack_start(self.oAuthor, False, True, 0)
        self.vbox.pack_start(self.oCommentWin, True, True, 0)
        self.vbox.pack_start(oParentLabel, False, True, 0)
        self.vbox.pack_start(AutoScrolledWindow(self.oParentList),
                             True, True, 0)
        self.vbox.pack_start(self.oAnnotateWin, True, True, 0)
        self.vbox.pack_start(self.oInUse, False, True, 0)

        self.connect("response", self.button_response)

        # We show the items before we fill in options to avoid the
        # "card set name is always completely selected" effect.
        self.show_all()

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

    def get_name(self):
        """Get the name entered by the user"""
        return self.sName

    def get_author(self):
        """Get the author value"""
        return self.sAuthor

    def get_comment(self):
        """Get the comment value"""
        sComment = self.oCommentWin.get_all_text()
        return sComment

    def get_annotations(self):
        """Get the comment value"""
        sAnnotations = self.oAnnotateWin.get_all_text()
        return sAnnotations

    def get_parent(self):
        """Get the chosen parent card set, or None if 'No Parent' is chosen"""
        return self.oParent

    def get_in_use(self):
        """Get the In Use checkbox status"""
        return self.oInUse.get_active()

    def button_response(self, _oWidget, iResponse):
        """Handle button press from the dialog."""
        if iResponse == Gtk.ResponseType.OK:
            self.sName = self.oName.get_text()
            self.sAuthor = self.oAuthor.get_text()
            if self.sName:
                # We don't allow < or > in the name, since pango uses that for
                # markup
                self.sName = self.sName.replace("<", "(")
                self.sName = self.sName.replace(">", ")")
                if self.sName != self.sOrigName:
                    # check if card set exists
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
