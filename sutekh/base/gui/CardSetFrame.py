# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Frame holding a CardSet
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Frame for holding Card Sets"""

from sqlobject import SQLObjectNotFound
from ..core.BaseObjects import PhysicalCardSet, IPhysicalCardSet
from .CardListFrame import CardListFrame
from .CardSetMenu import CardSetMenu
from .CardSetController import CardSetController


class CardSetFrame(CardListFrame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """class for Card Set frames.

       Handles most of the functionality - subclasses set the style name
       and the various other properties correctly for the type.
       """
    _cModelType = PhysicalCardSet

    def __init__(self, oMainWindow, sName, bStartEditable, cPCSWriter):
        super(CardSetFrame, self).__init__(oMainWindow)
        try:
            _oCS = IPhysicalCardSet(sName)
        except SQLObjectNotFound:
            raise RuntimeError("Card Set %s does not exist" % sName)
        self._oController = CardSetController(sName,
                                              oMainWindow, self,
                                              bStartEditable)
        self._sName = sName

        self.init_plugins()

        self._oMenu = CardSetMenu(self, self._oController, self._oMainWindow,
                                  cPCSWriter)
        self.set_name("physical card set card list")
        self.add_parts()

        self.update_name(sName)

    # pylint: disable-msg=W0212
    # We allow access via these properties
    name = property(fget=lambda self: self._sName, doc="Frame Name")
    cardset_name = property(fget=lambda self: self._oController.view.sSetName,
                            doc="Name of the card set for this frame")
    # pylint: enable-msg=W0212

    def cleanup(self, bQuit=False):
        """Cleanup function called before pane is removed by the Main Window"""
        super(CardSetFrame, self).cleanup(bQuit)
        # skip reloading the pcs list when we're exiting
        if not bQuit:
            self._oMainWindow.reload_pcs_list()
        # Clean up the signal handlers, to avoid problems
        self._oController.cleanup()

    def update_name(self, sNewName):
        """Update the frame name to the current card set name."""
        # Find an unused name for this card set
        iCount = 0
        sFinalName = sNewName
        aOtherOpenSets = [x.title for x in
                          self._oMainWindow.find_cs_pane_by_set_name(sNewName)
                          if x is not self]
        while sFinalName in aOtherOpenSets:
            iCount += 1
            sFinalName = "%s (%d)" % (sNewName, iCount)
        self._sName = sFinalName
        self.set_title(self._sName)

    def is_card_set(self, sSetName):
        """Return true if we're a copy of the given set"""
        return self.cardset_name == sSetName

    def update_to_new_db(self):
        """Re-associate internal data against the database.

           Needed for re-reading WW cardlists and such.
           Instruct controller + model to update themselves,
           then reload.
           """
        self._oController.update_to_new_db()
        self.reload()
