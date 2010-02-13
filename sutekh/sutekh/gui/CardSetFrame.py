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
from sutekh.gui.CardSetController import CardSetController
from sutekh.gui.CardSetListModel import IGNORE_PARENT

class CardSetFrame(CardListFrame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """class for Card Set frames.

       Handles most of the functionality - subclasses set the style name
       and the various other properties correctly for the type.
       """
    _cModelType = PhysicalCardSet

    def __init__(self, oMainWindow, sName, tInfo=None):
        super(CardSetFrame, self).__init__(oMainWindow)
        try:
            _oCS = IPhysicalCardSet(sName)
        except SQLObjectNotFound:
            raise RuntimeError("Card Set %s does not exist" % sName)
        self._oController = CardSetController(sName,
                oMainWindow, self)

        # pylint: disable-msg=E1101
        # PyProtocols confuses pylint here
        if tInfo:
            self.set_model_modes(tInfo)
        elif _oCS.parent and not _oCS.parent.cards:
            self._oController.model.iParentCountMode = IGNORE_PARENT
            # Else, we go with the defaults

        self._sName = sName

        self.init_plugins()

        self._oMenu = CardSetMenu(self, self._oController, self._oMainWindow)
        self.set_name("physical card set card list")
        self.add_parts()

        self.update_name(sName)

        self._oController.view.check_editable()

    # pylint: disable-msg=W0212
    # We allow access via these properties
    name = property(fget=lambda self: self._sName, doc="Frame Name")
    # pylint: enable-msg=W0212

    def cleanup(self):
        """Cleanup function called before pane is removed by the Main Window"""
        self._oMainWindow.reload_pcs_list()
        # Clean up the signal handlers, to avoid problems
        self._oController.cleanup()

    def update_name(self, sNewName):
        """Update the frame name to the current card set name."""
        # Find an unused name for this card set
        iCount = 0
        sFinalName = sNewName
        aOpenSets = [x.title for x in
                self._oMainWindow.find_cs_pane_by_set_name(sNewName)]
        while sFinalName in aOpenSets:
            iCount += 1
            sFinalName = "%s (%d)" % (sNewName, iCount)
        self._sName = sFinalName
        self.set_title(self._sName)

    def is_card_set(self, sSetName):
        """Return true if we're a copy of the given set"""
        return self._oController.view.sSetName == sSetName

    def update_to_new_db(self):
        """Re-associate internal data against the database.

           Needed for re-reading WW cardlists and such.
           Instruct controller + model to update themselves,
           then reload.
           """
        self._oController.update_to_new_db()
        self.reload()

    def get_model_modes(self):
        """Get the model modes"""
        return self._oController.model.iExtraLevelsMode, \
                self._oController.model.iParentCountMode, \
                self._oController.model.iShowCardMode

    def set_model_modes(self, tInfo):
        """Set the model + menu to the saved modes"""
        iExtraLevelsMode, iParentCountMode, iShowCardMode = tInfo
        self._oController.model.iExtraLevelsMode = iExtraLevelsMode
        self._oController.model.iParentCountMode = iParentCountMode
        self._oController.model.iShowCardMode = iShowCardMode

    def do_queued_reload(self):
        """Do a deferred reload if one was set earlier"""
        if self._bNeedReload:
            self.reload()
        self._bNeedReload = False

