# CardSetFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Frame holding a CardSet
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Frame for holding Card Sets"""

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, \
        IPhysicalCardSet, IAbstractCardSet
from sutekh.gui.CardListFrame import CardListFrame
from sutekh.gui.CardSetMenu import CardSetMenu
from sutekh.gui.CardSetController import PhysicalCardSetController, \
        AbstractCardSetController

class CardSetFrame(CardListFrame, object):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Base class for Card Set frames.

       Handles most of the functionality - subclasses set the style name
       and the various other properties correctly for the type.
       """
    _cModelType = None

    def __init__(self, oMainWindow, sName):
        super(CardSetFrame, self).__init__(oMainWindow)
        try:
            # pylint: disable-msg=W0612
            # oCS just used for existance test, so ignored
            if self._cModelType is PhysicalCardSet:
                oCS = IPhysicalCardSet(sName)
            else:
                oCS = IAbstractCardSet(sName)
        except SQLObjectNotFound:
            raise RuntimeError("Card Set %s does not exist" % sName)
        if self._cModelType is PhysicalCardSet:
            self._oController = PhysicalCardSetController(sName,
                    oMainWindow, self)
        elif self._cModelType is AbstractCardSet:
            self._oController = AbstractCardSetController(sName,
                    oMainWindow, self)
        else:
            raise RuntimeError("Unknown Card Set type %s" % self._cModelType)

        self.init_plugins()

        self._oMenu = CardSetMenu(self, self._oController, self._oMainWindow,
                self._oController.view, sName, self._cModelType)
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
        if self._cModelType is PhysicalCardSet:
            self._oMainWindow.reload_pcs_list()
        else:
            self._oMainWindow.reload_acs_list()

    def update_name(self, sNewName):
        """Update the frame name to the current card set name."""
        # pylint: disable-msg=W0201
        # this is called from __init__, so OK
        self.sSetName = sNewName
        self._sName = sNewName
        if self._cModelType is PhysicalCardSet:
            self.set_title('PCS:' + self.sSetName)
        else:
            self.set_title('ACS:' + self.sSetName)

    def delete_card_set(self):
        """Delete this card set from the database"""
        if self._oController.view.delete_card_set():
            # Card Set was deleted, so close up
            self.close_frame()

class AbstractCardSetFrame(CardSetFrame):
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods
    """Card Set Frame for holding Abstract Card Sets."""
    _cModelType = AbstractCardSet
    def __init__(self, oMainWindow, sName):
        super(AbstractCardSetFrame, self).__init__(oMainWindow, sName)
        self.set_name("abstract card set card list")

class PhysicalCardSetFrame(CardSetFrame):
    # pylint: disable-msg=R0904
    # R0904 - gtk.Widget, so many public methods
    """Card Set Frame for holding Physical Card Sets."""
    _cModelType = PhysicalCardSet
    def __init__(self, oMainWindow, sName):
        super(PhysicalCardSetFrame, self).__init__(oMainWindow, sName)
        self.set_name("physical card set card list")
