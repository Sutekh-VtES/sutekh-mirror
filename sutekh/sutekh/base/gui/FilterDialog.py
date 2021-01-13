# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006, 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Allow the user to specify a filter."""

from gi.repository import GObject, Gtk

from ..core import FilterParser
from .SutekhDialog import (SutekhDialog, do_complaint_error,
                           do_complaint_buttons)
from .BaseConfigFile import FULL_CARDLIST, CARDSET, DEF_PROFILE_FILTER
from .MessageBus import MessageBus
from .FilterEditor import FilterEditor


class FilterDialog(SutekhDialog):
    """Dialog which allows the user to select and edit filters.

       This dialog exists per card list view, and keeps state during
       a session by never being destoryed - just hiding itself when
       needed.

       This also listens to Config File events, so the list of available
       filters remains syncronised across the different views.
       """
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # we keep a lot of internal state, so many instance variables
    # Gtk.Widget, so many public methods

    RESPONSE_CLEAR = 1
    RESPONSE_REVERT = 2
    RESPONSE_LOAD = 3
    RESPONSE_SAVE = 4
    RESPONSE_DELETE = 5

    INITIAL_FILTER = "Default Filter Template"

    def __init__(self, oParent, oConfig, sFilterType, sDefaultFilter=None):
        super().__init__("Specify Filter", oParent,
                         Gtk.DialogFlags.DESTROY_WITH_PARENT)

        self._oAccelGroup = Gtk.AccelGroup()
        self.__oParent = oParent
        self.__bWasCancelled = False
        self.__oParser = FilterParser.FilterParser()
        self.__oConfig = oConfig
        self.__sFilterType = sFilterType
        self.__oFilter = None
        self.__oFilterEditor = FilterEditor(None, self.__sFilterType,
                                            self.__oParser, self)
        self.__oFilterEditor.connect_name_changed(self.__name_changed)

        self.__sOriginalName = None
        self.__sOriginalAST = None

        self.set_default_size(700, 550)
        self.connect("response", self.__button_response)

        self._aDefaultFilters = oConfig.get_default_filters()

        # Dialog Buttons
        self.add_button("Clear Filter", self.RESPONSE_CLEAR)
        self.add_button("Revert Filter", self.RESPONSE_REVERT)
        self.add_button("Load", self.RESPONSE_LOAD)
        self.add_button("Save", self.RESPONSE_SAVE)
        self.add_button("Delete", self.RESPONSE_DELETE)

        self.action_area.pack_start(Gtk.VSeparator(), True, True, 0)

        self.add_button("_OK", Gtk.ResponseType.OK)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)

        self.vbox.pack_start(self.__oFilterEditor, True, True, 0)

        # set initial filter

        aDefaultFilters = self.__fetch_filters(True)
        aConfigFilters = self.__fetch_filters(False)

        if sDefaultFilter:
            # Ensure filter isn't broken
            # pylint: disable=broad-except
            # we do want to catch all exceptions here
            try:
                oAST = self.__oParser.apply(sDefaultFilter)
            except Exception:
                # Fall back to usual behaviour
                sDefaultFilter = None

        if sDefaultFilter:
            sName, sFilter = "", sDefaultFilter
            oAST = self.__oParser.apply(sFilter)
        elif aDefaultFilters:
            sName, sFilter = aDefaultFilters[0]
            oAST = self.__oParser.apply(sFilter)
        elif aConfigFilters:
            sName, sFilter = aConfigFilters[0]
            oAST = self.__oParser.apply(sFilter)
        else:
            sName, oAST = "", None

        self.__load_filter(sName, oAST)

        self.add_accel_group(self._oAccelGroup)

        MessageBus.subscribe(MessageBus.Type.CONFIG_MSG, 'replace_filter',
                             self.replace_filter)
        MessageBus.subscribe(MessageBus.Type.CONFIG_MSG, 'add_filter',
                             self.add_filter)
        MessageBus.subscribe(MessageBus.Type.CONFIG_MSG, 'remove_filter',
                             self.remove_filter)

        self.show_all()

    # pylint: disable=protected-access
    # explicitly allow access to these values via thesep properties
    accel_group = property(fget=lambda self: self._oAccelGroup,
                           doc="Dialog Accelerator group")
    # pylint: enable=protected-access

    def __button_response(self, _oWidget, iResponse):
        """Handle the button choices from the user.

           If the operation doesn't close the dialog, such as the
           filter manipulation options, we short circuit the signal
           handling, and prevent anything propogating to the
           window waiting for the dialog.
           """
        if iResponse == Gtk.ResponseType.OK:
            # construct the final filter (may be None)
            self.__bWasCancelled = False
            self.__oFilter = self.__oFilterEditor.get_filter()
        elif iResponse == self.RESPONSE_CLEAR:
            # clear the  filter editor
            self.__clear_filter()
            return True
        elif iResponse == self.RESPONSE_REVERT:
            # revert the filter editor AST to the saved version
            self.__revert_filter()
            return True
        elif iResponse == self.RESPONSE_LOAD:
            # present the load filter dialog and handle result
            self.__run_load_dialog()
            return True
        elif iResponse == self.RESPONSE_SAVE:
            # save the filter editor ast to the config file
            self.__save_filter()
            return True
        elif iResponse == self.RESPONSE_DELETE:
            # delete the copy of the filter in the config file
            # and clear the filter editor
            self.__delete_filter()
            return True
        else:
            self.__bWasCancelled = True
        self.hide()
        # propogate signal
        return False

    def __run_load_dialog(self):
        """Display a dialog for loading a filter."""
        oLoadDialog = SutekhDialog("Load Filter", self.__oParent,
                                   Gtk.DialogFlags.MODAL |
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT)

        oLoadDialog.set_keep_above(True)

        oLoadDialog.add_button("_OK", Gtk.ResponseType.OK)
        oLoadDialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)

        # default (True or False), filter name (str), query string (str)
        oFilterStore = Gtk.ListStore(GObject.TYPE_BOOLEAN, GObject.TYPE_STRING,
                                     GObject.TYPE_STRING)

        def iter_to_text(_oLayout, oCell, oModel, oIter):
            """Convert the model entry at oIter into the correct text"""
            bDefault = oModel.get_value(oIter, 0)
            sName = oModel.get_value(oIter, 1)
            if bDefault:
                oCell.set_property('text', sName + " (built-in)")
            else:
                oCell.set_property('text', sName)

        for bDefault in (True, False):
            for sName, sFilter in self.__fetch_filters(bDefault):
                oIter = oFilterStore.append(None)
                oFilterStore.set(oIter, 0, bDefault, 1, sName, 2, sFilter)

        oFilterSelector = Gtk.ComboBox()
        oFilterSelector.set_model(oFilterStore)

        oCell = Gtk.CellRendererText()
        oFilterSelector.pack_start(oCell, True)
        oFilterSelector.set_cell_data_func(oCell, iter_to_text)

        oLoadDialog.vbox.pack_start(oFilterSelector, True, True, 0)
        oLoadDialog.show_all()

        try:
            iResponse = oLoadDialog.run()
            oIter = oFilterSelector.get_active_iter()

            if iResponse == Gtk.ResponseType.OK and oIter:
                sName = oFilterStore.get_value(oIter, 1)
                sFilter = oFilterStore.get_value(oIter, 2)
                oAST = self.__oParser.apply(sFilter)
                self.__load_filter(sName, oAST)
        finally:
            oLoadDialog.destroy()

    def __fetch_filters(self, bDefault):
        """Load filters from config or default list.

           Returns a (sName, sFilter) list.
           """
        if bDefault:
            sSrc = "default filter list"
            oFilterIter = list(self._aDefaultFilters.items())
        else:
            sSrc = "config file"
            oFilterIter = list(self.__oConfig.get_filter_keys())

        aFilters = []
        aErrMsgs = []

        for sName, sFilter in oFilterIter:
            # pylint: disable=broad-except
            # we do want to catch all exceptions here
            try:
                oAST = self.__oParser.apply(sFilter)
                if sName.lower() == DEF_PROFILE_FILTER.lower():
                    # jump into the error path
                    raise RuntimeError('Reserved name used for filter name')
                if (oAST.get_filter_expression() is None or
                        self.__sFilterType in oAST.get_type()):
                    aFilters.append((sName, sFilter))
            except Exception:
                # remove broken filter
                aErrMsgs.append("%s (filter: '%s')" % (sName, sFilter))
                if not bDefault:
                    self.__oConfig.remove_filter(sFilter, sName)
                else:
                    del self._aDefaultFilters[sName]

        if aErrMsgs:
            do_complaint_error("The following invalid filters have been"
                               " removed from the %s:\n" % (sSrc,)
                               + "\n".join(aErrMsgs))

        def filter_key(tFiltInfo):
            """We sort filters alphabetically by name, but with default
               filter first if it is present"""
            if tFiltInfo[0] == self.INITIAL_FILTER:
                # Return empty string, so we sort ahead of everything else
                # Should be safe, since we don't allow empty names for
                # filters
                return ''
            return tFiltInfo[0]

        aFilters.sort(key=filter_key)

        return aFilters

    def __load_filter(self, sName, oAST):
        """Set the current filter to sName, oAST."""
        self.__sOriginalName = sName
        self.__sOriginalAST = oAST
        self.__oFilterEditor.set_name(sName)
        self.__oFilterEditor.replace_ast(oAST)
        self.__update_sensitivity()

    def __revert_filter(self):
        """Revert the filter to the last one set."""
        self.__oFilterEditor.set_name(self.__sOriginalName)
        self.__oFilterEditor.replace_ast(self.__sOriginalAST)
        self.__update_sensitivity()

    def __clear_filter(self):
        """Clear the filter AST."""
        self.__oFilterEditor.set_name("")
        self.__oFilterEditor.replace_ast(None)
        self.__update_sensitivity()

    def __save_filter(self):
        """Save the filter to the config."""
        sName = self.__oFilterEditor.get_name()
        sFilter = self.__oFilterEditor.get_current_text()
        sConfigFilter = self.__oConfig.get_filter(sName)
        bSaved = False

        if sName.lower() == DEF_PROFILE_FILTER.lower():
            do_complaint_error("%s is a reserved filter name.\nNot Saving" %
                               sName)
            return

        if sConfigFilter is not None:
            iResponse = do_complaint_buttons(
                "Replace existing filter '%s'?" % (sName,),
                Gtk.MessageType.QUESTION,
                ("Yes", Gtk.ResponseType.YES,
                 "No", Gtk.ResponseType.NO))
            if iResponse == Gtk.ResponseType.YES:
                self.__oConfig.replace_filter(sName, sConfigFilter, sFilter)
                bSaved = True
        else:
            self.__oConfig.add_filter(sName, sFilter)
            bSaved = True

        if bSaved:
            # Update list for profiles
            self.__oConfig.update_filter_list()
            # load saved filter to set everything correctly
            oAST = self.__oParser.apply(sFilter)
            self.__load_filter(sName, oAST)

    def __delete_filter(self):
        """Delete the filter from the config."""
        sName = self.__oFilterEditor.get_name()
        sConfigFilter = self.__oConfig.get_filter(sName)

        dProfiles = self.__oConfig.get_profiles_for_filter(sName)

        if sConfigFilter is not None:
            if dProfiles[FULL_CARDLIST] or dProfiles[CARDSET]:
                # Filter is in use as a config filter, so prompt
                sCardlist = '\n'.join([
                    'Cardlist profile : %s' %
                    self.__oConfig.get_profile_option(FULL_CARDLIST, x, 'name')
                    for x in dProfiles[FULL_CARDLIST]])
                sCardset = '\n'.join([
                    'Cardset profile : %s' %
                    self.__oConfig.get_profile_option(CARDSET, x, 'name')
                    for x in dProfiles[CARDSET]])
                sProfiles = '\n'.join([sCardlist, sCardset])
                iResponse = do_complaint_buttons(
                    "Filter '%s' used in the followin profiles:\n%s\n"
                    "Really delete?" % (sName, sProfiles),
                    Gtk.MessageType.QUESTION, ("Yes", Gtk.ResponseType.YES,
                                               "No", Gtk.ResponseType.NO))
                if iResponse == Gtk.ResponseType.YES:
                    self.__oConfig.remove_filter(sName, sConfigFilter)
                else:
                    # Cancelled, so skip out
                    return
            else:
                # Not in use, just delete
                self.__oConfig.remove_filter(sName, sConfigFilter)

        self.__load_filter("", None)
        # Update list for profiles
        self.__oConfig.update_filter_list()

    def __update_sensitivity(self):
        """Update which responses are available."""
        # clear, revert and load are always available

        sName = self.__oFilterEditor.get_name()
        sConfigFilter = self.__oConfig.get_filter(sName)

        # save is available unless there is no name to save as
        if sName:
            self.set_response_sensitive(self.RESPONSE_SAVE, True)
        else:
            self.set_response_sensitive(self.RESPONSE_SAVE, False)

        # delete is available if the name is unchanged and the
        # original name exists in the config
        if sName == self.__sOriginalName and sConfigFilter is not None:
            self.set_response_sensitive(self.RESPONSE_DELETE, True)
        else:
            self.set_response_sensitive(self.RESPONSE_DELETE, False)

    def __name_changed(self, _oNameEntry):
        """Callback for connecting to filter editor name change events."""
        self.__update_sensitivity()

    # Dialog result retrievel methods

    def get_filter(self):
        """Get the current filter for this dialog."""
        return self.__oFilter

    def was_cancelled(self):
        """Return true if the user cancelled the filter dialog."""
        return self.__bWasCancelled

    # Config File Listener methods
    def replace_filter(self, _sId, _sOldFilter, _sNewFilter):
        """Handle a filter in the config file being replaced."""
        self.__update_sensitivity()

    def add_filter(self, _sId, _sFilter):
        """Handle filter being added to the config file."""
        self.__update_sensitivity()

    def remove_filter(self, _sId, _sFilter):
        """Handle a filter being removed from the config file."""
        self.__update_sensitivity()
