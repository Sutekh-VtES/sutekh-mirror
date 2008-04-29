# CardSetFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Frame holding a CardSet
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Frame for holding Card Sets"""

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet, \
        IPhysicalCardSet
from sutekh.gui.CardListFrame import CardListFrame
from sutekh.gui.CardSetMenu import CardSetMenu
from sutekh.gui.CardSetController import PhysicalCardSetController

class CardSetFrame(CardListFrame, object):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Base class for Card Set frames.

       Handles most of the functionality - subclasses set the style name
       and the various other properties correctly for the type.
       """
    def __init__(self, oMainWindow, sName):
        super(CardSetFrame, self).__init__(oMainWindow)
        try:
            # pylint: disable-msg=W0612
            # oCS just used for existance test, so ignored
            oCS = IPhysicalCardSet(sName)
        except SQLObjectNotFound:
            raise RuntimeError("Card Set %s does not exist" % sName)
        self._oController = PhysicalCardSetController(sName,
                oMainWindow, self)

        self._cModelType = PhysicalCardSet

        self.init_plugins()

        self._oMenu = CardSetMenu(self, self._oController, self._oMainWindow,
                sName)
        self.add_parts()

        self.update_name(sName)

        self._oController.view.check_editable()

    # pylint: disable-msg=W0212
    # We allow access via these properties
    name = property(fget=lambda self: self._sName, doc="Frame Name")
    # pylint: enable-msg=W0212

    def cleanup(self):
        """
        Cleanup function called before pane is removed by the
        Main Window
        """
        self._oMainWindow.reload_pcs_list()

    def update_name(self, sNewName):
        """Update the frame name to the current card set name."""
        # pylint: disable-msg=W0201
        # this is called from __init__, so OK
        self.sSetName = sNewName
        self._sName = sNewName
        self.set_title(self.sSetName)

    def delete_card_set(self):
        """Delete this card set from the database"""
        if self._oController.view.delete_card_set():
            # Card Set was deleted, so close up
            self.close_frame()

class PhysicalCardSetFrame(CardSetFrame):
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods
    """Card Set Frame for holding Physical Card Sets."""
    def __init__(self, oMainWindow, sName):
        super(PhysicalCardSetFrame, self).__init__(oMainWindow, sName)
        self.set_name("physical card set card list")
