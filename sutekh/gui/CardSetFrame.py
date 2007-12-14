# CardSetFrame.py
# Frame holding a CardSet 
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet, \
        IPhysicalCardSet, IAbstractCardSet
from sutekh.gui.CardListFrame import CardListFrame
from sutekh.gui.CardSetMenu import CardSetMenu
from sutekh.gui.CardSetController import PhysicalCardSetController, \
        AbstractCardSetController

class CardSetFrame(CardListFrame, object):
    def __init__(self, oMainWindow, sName, cType, oConfig):
        super(CardSetFrame, self).__init__(oMainWindow, oConfig)
        self._cModelType = cType
        try:
            if self._cModelType is PhysicalCardSet:
                oCS = IPhysicalCardSet(sName)
            else:
                oCS = IAbstractCardSet(sName)
        except SQLObjectNotFound:
            raise RuntimeError("Card Set %s does not exist" % sName)
        if self._cModelType is PhysicalCardSet:
            self._oC = PhysicalCardSetController(sName, oConfig,
                    oMainWindow, self)
        elif self._cModelType is AbstractCardSet:
            self._oC = AbstractCardSetController(sName, oConfig,
                    oMainWindow, self)
        else:
            raise RuntimeError("Unknown Card Set type %s" % str(cType))

        self.init_plugins()

        self._oMenu = CardSetMenu(self, self._oC, self._oMainWindow, self._oC.view,
                sName, self._cModelType)
        self.add_parts()

        self.update_name(sName)


    name = property(fget=lambda self: self._sName, doc="Frame Name")

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
        self.sSetName = sNewName
        self._sName = sNewName
        if self._cModelType is PhysicalCardSet:
            self.set_title('PCS:' + self.sSetName)
        else:
            self.set_title('ACS:' + self.sSetName)

    def deleteCardSet(self):
        if self._oC.view.deleteCardSet():
            # Card Set was deleted, so close up
            self.close_frame()

class AbstractCardSetFrame(CardSetFrame):
    def __init__(self, oMainWindow, sName, oConfig):
        super(AbstractCardSetFrame, self).__init__(oMainWindow, sName, 
                AbstractCardSet, oConfig)
        self.set_name("abstract card set card list")

class PhysicalCardSetFrame(CardSetFrame):
    def __init__(self, oMainWindow, sName, oConfig):
        super(PhysicalCardSetFrame, self).__init__(oMainWindow, sName, 
                PhysicalCardSet, oConfig)
        self.set_name("physical card set card list")
