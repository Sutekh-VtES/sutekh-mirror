# CardSetManagementFrame.py
# Window for Managing Physical and Abstract Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import SQLObjectNotFound
from sqlobject.events import listen, RowDestroySignal, \
        RowCreatedSignal, RowUpdateSignal
from sutekh.SutekhUtility import delete_physical_card_set, delete_abstract_card_set
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.core.Filters import NullFilter
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog

class CardSetManagementFrame(gtk.Frame, object):

    __sOpen = "<b>Opened</b>"
    __sAvail = "<b>Available</b>"

    def __init__(self, oMainWindow, oConfig):
        super(CardSetManagementFrame, self).__init__()
        self._oMainWindow = oMainWindow
        self._oConfig = oConfig
        self._cSetType = None
        self._sName = 'Card Set List'
        self._oView = None
        self._oMenu = gtk.MenuBar()
        self._oFilter = NullFilter()
        self._oFilterDialog = None
        self._sFilterType = None

    name = property(fget=lambda self: self._sName, doc="Frame Name")
    view = property(fget=lambda self: self._oView, doc="Associated View Object")
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")

    def add_actions_menu(self):
        iMenu = gtk.MenuItem(self._sName + ' Actions')
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        sSetName = self._sName.replace(' List', '')
        iCreate = gtk.MenuItem('Create New ' + sSetName)
        wMenu.add(iCreate)
        iCreate.connect('activate', self.create_new_card_set)
        iDelete = gtk.MenuItem('Delete selected ' + sSetName)
        wMenu.add(iDelete)
        iDelete.connect('activate', self.delete_card_set)
        iSep = gtk.SeparatorMenuItem()
        wMenu.add(iSep)
        iClose = gtk.MenuItem('Close Pane')
        wMenu.add(iClose)
        iClose.connect('activate', self.close_menu_item)
        self._oMenu.add(iMenu)

    def add_filter_menu(self):
        iMenu = gtk.MenuItem('Filter')
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        iFilter = gtk.MenuItem('Specify Filter')
        wMenu.add(iFilter)
        iFilter.connect('activate', self.set_filter)
        self.iApply = gtk.CheckMenuItem('Apply Filter')
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('toggled', self.toggle_apply)
        self._oMenu.add(iMenu)

    def cleanup(self):
        pass

    def reload(self):
        pass

    def close_pane(self):
        self._oMainWindow.remove_pane(self)
        self.destroy()

    def close_menu_item(self, oMenuWidget):
        self.close_pane()

    def add_parts(self):
        """Add a list object to the frame"""
        wMbox = gtk.VBox(False, 2)

        self.__oTitle = gtk.Label(self._sName)
        wMbox.pack_start(self.__oTitle, False, False)

        self.add_actions_menu()
        self.add_filter_menu()

        wMbox.pack_start(self._oMenu, False, False)

        self._oScrolledList = ScrolledList(self._sName)
        self._oView = self._oScrolledList.view
        self._oScrolledList.set_select_single()
        self._oView.connect('row_activated', self.row_clicked)
        self.reload_card_set_list()
        wMbox.pack_start(self._oScrolledList, expand=True)
        self.add(wMbox)
        self.show_all()

        self.__oBaseStyle = self.__oTitle.get_style().copy()
        self.__oFocStyle = self.__oTitle.get_style().copy()
        oMap = self.__oTitle.get_colormap()
        oHighlighted = oMap.alloc_color("purple")
        self.__oFocStyle.fg[gtk.STATE_NORMAL] = oHighlighted

    def set_focussed_title(self):
        self.__oTitle.set_style(self.__oFocStyle)

    def set_unfocussed_title(self):
        self.__oTitle.set_style(self.__oBaseStyle)

    def create_new_card_set(self, oWidget):
        if self._cSetType is PhysicalCardSet:
            oDialog = CreateCardSetDialog(self._oMainWindow, 'Physical')
            open_card_set = self._oMainWindow.add_physical_card_set
        else:
            oDialog = CreateCardSetDialog(self._oMainWindow, 'Abstract')
            open_card_set = self._oMainWindow.add_abstract_card_set
        oDialog.run()
        (sName, sAuthor, sDescription) = oDialog.get_data()
        oDialog.destroy()
        if sName is not None:
            iCnt = self._cSetType.selectBy(name=sName).count()
            if iCnt > 0:
                oComplaint = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE, "Chosen Card Set Name is already in use.")
                oComplaint.run()
                oComplaint.destroy()
            else:
                oCS = self._cSetType(name=sName, author=sAuthor, comment=sDescription)
                open_card_set(sName)

    def delete_card_set(self, oWidget):
        aSelection = self._oScrolledList.get_selection()
        if len(aSelection) != 1:
            return
        else:
            sSetName = aSelection[0]
        try:
            oCS = self._cSetType.byName(sSetName)
        except SQLObjectNotFound:
            return
        if len(oCS.cards) > 0:
            oDialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_OK_CANCEL, "Card Set " + sSetName +
                    " Not Empty. Really Delete?")
            iResponse = oDialog.run()
            oDialog.destroy()
            if iResponse == gtk.RESPONSE_CANCEL:
                # Don't delete
                return
        # Got here, so delete the card set
        if self._cSetType is PhysicalCardSet:
            sPaneName = 'PCS:' + sSetName
            delete_physical_card_set(sSetName)
        else:
            sPaneName = 'ACS:' + sSetName
            delete_abstract_card_set(sSetName)
        self._oMainWindow.remove_pane_by_name(sPaneName)
        self.reload_card_set_list()

    def reload_card_set_list(self):
        aVals = [self.__sOpen, self.__sAvail]
        iAvailIndex = 1
        if self.iApply.active:
            oSelectFilter = self._oFilter
        else:
            oSelectFilter = NullFilter()
        for oCS in oSelectFilter.select(self._oSetClass).orderBy('name'):
            if self._cSetType is PhysicalCardSet:
                sPaneName = 'PCS:' + oCS.name
            else:
                sPaneName = 'ACS:' + oCS.name
            if sPaneName not in self._oMainWindow.dOpenPanes.values():
                aVals.append(oCS.name)
            else:
                aVals.insert(iAvailIndex, oCS.name)
                iAvailIndex += 1
        self._oScrolledList.fill_list(aVals)

    def set_filter(self, oWidget):
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWindow, self._oConfig, self._sFilterType)

        self._oFilterDialog.run()

        if self._oFilterDialog.Cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.getFilter()
        if oFilter != None:
            self._oFilter = oFilter
            if self.iApply.active:
                self.reload_card_set_list()
            else:
                # Let toggle reload for us
                self.set_apply_filter(True)
        else:
            self._oFilter = NullFilter()
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if not self.iApply.active:
                self.reload_card_set_list()
            else:
                # Let toggle reload for us
                self.set_apply_filter(False)

    def set_apply_filter(self, bState):
        self.iApply.set_active(bState)

    def toggle_apply(self, oWidget):
        self.reload_card_set_list()

    def row_clicked(self, oTreeView, oPath, oColumn):
        oM = oTreeView.get_model()
        # We are pointing to a ListStore, so the iters should always be valid
        # Need to dereference to the actual path though, as iters not unique
        oIter = oM.get_iter(oPath)
        sName = oM.get_value(oIter, 0)
        if sName == self.__sAvail or sName == self.__sOpen:
            return
        if self._cSetType is PhysicalCardSet:
            self._oMainWindow.add_physical_card_set(sName)
        elif self._cSetType is AbstractCardSet:
            self._oMainWindow.add_abstract_card_set(sName)

class PhysicalCardSetListFrame(CardSetManagementFrame):
    def __init__(self, oMainWindow, oConfig):
        super(PhysicalCardSetListFrame, self).__init__(oMainWindow, oConfig)
        self._cSetType = PhysicalCardSet
        self._sFilterType = 'PhysicalCardSet'
        self._sName = 'Physical Card Set List'
        self._oSetClass = PhysicalCardSet
        self.add_parts()

class AbstractCardSetListFrame(CardSetManagementFrame):
    def __init__(self, oMainWindow, oConfig):
        super(AbstractCardSetListFrame, self).__init__(oMainWindow, oConfig)
        self._cSetType = AbstractCardSet
        self._sFilterType = 'AbstractCardSet'
        self._sName = 'Abstract Card Set List'
        self._oSetClass = AbstractCardSet
        self.add_parts()


