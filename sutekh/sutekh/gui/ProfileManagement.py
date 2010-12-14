# ProfileManagement.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for deleting / editing the different profiles
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Allow the user to delete / edit the various profiles"""

import gtk
import gobject
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error, \
                                    do_complaint_warning
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.FrameProfileEditor import FrameProfileEditor
from sutekh.gui.ConfigFile import ConfigFileListener, CARDSET, WW_CARDLIST, \
        CARDSET_LIST

LABELS = {
        CARDSET: 'Card Set Profiles',
        WW_CARDLIST: 'White Wolf Cardlist Profiles',
        CARDSET_LIST: 'Card Set List Profiles',
        }


class ProfileListStore(gtk.ListStore):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Simple list store for profiles widget"""
    def __init__(self):
        super(ProfileListStore, self).__init__(gobject.TYPE_STRING,
                gobject.TYPE_STRING)

    def fill_list(self, aVals):
        """Fill the list"""
        self.clear()
        for tEntry in aVals:
            self.append(row=tEntry)

    def _find_iter(self, sProfile):
        """Find the correct iter for an entry"""
        oIter = self.get_iter_root()
        while oIter:
            if sProfile == self.get_value(oIter, 0):
                return oIter
            oIter = self.iter_next(oIter)
        return None  # fell off the end

    def fix_entry(self, sProfile, sNewName):
        """Fix the value for the given profile"""
        oIter = self._find_iter(sProfile)
        if oIter:
            self.set_value(oIter, 1, sNewName)

    def remove_entry(self, sProfile):
        """Fix the value for the given profile"""
        oIter = self._find_iter(sProfile)
        if oIter:
            self.remove(oIter)


class ProfileListView(gtk.TreeView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Simple tree view for the profile list"""
    def __init__(self, sTitle):
        oModel = ProfileListStore()
        super(ProfileListView, self).__init__(oModel)
        # We only display the profile name, not the profile id
        oCell1 = gtk.CellRendererText()
        oColumn1 = gtk.TreeViewColumn(sTitle, oCell1, text=1)
        self.append_column(oColumn1)
        self.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def get_selected(self):
        """Get the of selected value"""
        oModel, aSelectedRows = self.get_selection().get_selected_rows()
        for oPath in aSelectedRows:
            oIter = oModel.get_iter(oPath)
            sProfile = oModel.get_value(oIter, 0)
            sName = oModel.get_value(oIter, 1)
            return (sProfile, sName)
        return None


class ScrolledProfileList(gtk.Frame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Frame containing the scrolled list of profiles"""
    def __init__(self, sTitle):
        super(ScrolledProfileList, self).__init__(None)
        self._oView = ProfileListView(sTitle)
        self._oStore = self._oView.get_model()
        oMyScroll = AutoScrolledWindow(self._oView)
        self.add(oMyScroll)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.show_all()

    # pylint: disable-msg=W0212
    # allow access via these properties
    store = property(fget=lambda self: self._oStore, doc="List of values")
    view = property(fget=lambda self: self._oView, doc="List of values")
    # disable-msg=W0212


class ProfileMngDlg(SutekhDialog, ConfigFileListener):
    """Dialog which allows the user to delete and edit profiles."""
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we keep a lot of internal state, so many instance variables

    RESPONSE_EDIT = 1
    RESPONSE_DELETE = 2

    def __init__(self, oParent, oConfig):
        super(ProfileMngDlg, self).__init__("Manage Profiles",
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.__oParent = oParent
        self.__oConfig = oConfig
        self._dLists = {}

        # Add Listener, so we catch changes in future
        oConfig.add_listener(self)

        self.set_default_size(700, 550)

        self._oNotebook = gtk.Notebook()
        self._oNotebook.set_scrollable(True)
        self._oNotebook.popup_enable()
        for sType in (CARDSET, WW_CARDLIST, CARDSET_LIST):
            oProfileList = self._make_profile_list(sType)
            self._oNotebook.append_page(oProfileList, gtk.Label(LABELS[sType]))
            self._dLists[oProfileList] = sType

        # pylint: disable-msg=E1101
        # vbox, action_area confuse pylint
        self.vbox.pack_start(self._oNotebook)
        # Add buttons
        self.add_button("Edit Profile", self.RESPONSE_EDIT)
        self.add_button("Delete", self.RESPONSE_DELETE)

        self.action_area.pack_start(gtk.VSeparator(), expand=True)

        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

        self.connect("response", self._button_response)

        self.show_all()

    def _make_profile_list(self, sType):
        """Create a list of the available profiles"""
        oList = ScrolledProfileList(LABELS[sType])
        aProfiles = set(self.__oConfig.profiles(sType))
        aNames = [('defaults', 'Default')]
        for sProfile in list(sorted(aProfiles)):
            sName = self.__oConfig.get_profile_option(sType, sProfile, 'name')
            aNames.append((sProfile, sName))
        oList.store.fill_list(aNames)
        return oList

    def _button_response(self, _oWidget, iResponse):
        """Handle the button choices from the user.

           If the operation doesn't close the dialog we rerun the main
           dialog loop, waiting for another user button press (same
           logic as FilterDialog).
           """
        if iResponse == self.RESPONSE_EDIT:
            self._edit_profile()
            return self.run()
        elif iResponse == self.RESPONSE_DELETE:
            self._delete_profile()
            return self.run()
        # else CLOSE was pressed, so exit
        return iResponse

    def _get_cur_list(self):
        """Ensure list stores reflect the correct state"""
        iPageNum = self._oNotebook.get_current_page()
        return self._oNotebook.get_nth_page(iPageNum)

    def _get_selected_profile(self):
        """Get the currently selected profile and type"""
        oList = self._get_cur_list()
        sType = self._dLists[oList]
        tSelected = oList.view.get_selected()
        if tSelected:
            sProfile, sName = tSelected
        else:
            sProfile, sName = None, None
        return sType, sProfile, sName

    def _edit_profile(self):
        """Fire off the profile editor"""
        sType, sProfile, sName = self._get_selected_profile()
        if sProfile:
            sOldName = sName
            oEditDlg = FrameProfileEditor(self.__oParent, self.__oConfig,
                    sType)
            oEditDlg.set_selected_profile(sProfile)
            oEditDlg.run()
            sNewName = self.__oConfig.get_profile_option(sType, sProfile,
                    'name')
            if sNewName != sOldName:
                oList = self._get_cur_list()
                oList.store.fix_entry(sProfile, sNewName)

    def _get_in_use_mesg(self, sType, aPanes):
        """Return a suitable 'profile in use' message for profile deletion"""
        if sType in (CARDSET_LIST, WW_CARDLIST):
            return 'Profile is in use. Really delete?'
        else:
            # card set pane, so find names
            aOpenPanes = []
            aClosedPanes = []
            for sId in aPanes:
                if sId.startswith('cs'):
                    iCSid = int(sId[2:])  # cs<num>
                    # lookup name for card set id
                    try:
                        oCS = PhysicalCardSet.get(iCSid)
                    except SQLObjectNotFound:
                        # Remove defunct profile entry from the config
                        # file
                        self.__oConfig. clear_cardset_profile(sId)
                        continue
                    aCSPanes = self.__oParent.find_cs_pane_by_set_name(
                            oCS.name)
                    if aCSPanes:
                        for oPane in aCSPanes:
                            aOpenPanes.append(oPane.title)
                    else:
                        aClosedPanes.append(oCS.name)
                else:
                    iPaneId = int(sId[4:])  # pane<num>
                    oCSFrame = self.__oParent.find_pane_by_id(iPaneId)
                    aOpenPanes.append(oCSFrame.title)
            sMesg = "This profile is in use. Really delete?\n"
            if aOpenPanes:
                sMesg += '\nThe following open panes reference this ' \
                        ' profile\n' + '\n'.join(aOpenPanes)
            if aClosedPanes:
                sMesg += '\nThe following card closed card sets ' \
                        'reference this profile\n' + \
                        '\n'.join(aClosedPanes)
            return sMesg

    def _delete_profile(self):
        """Delete the given profile"""
        sType, sProfile, _sName = self._get_selected_profile()
        if sProfile:
            if sProfile == 'defaults':
                do_complaint_error("You can't delete the default profile")
                return
            aPanes = self.__oConfig.get_profile_users(sType, sProfile)
            if aPanes:
                sMesg = self._get_in_use_mesg(sType, aPanes)
                iRes = do_complaint_warning(sMesg)
                if iRes == gtk.RESPONSE_CANCEL:
                    return
            self.__oConfig.remove_profile(sType, sProfile)
            oList = self._get_cur_list()
            oList.store.remove_entry(sProfile)
