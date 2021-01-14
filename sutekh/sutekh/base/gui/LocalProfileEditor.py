# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Dialog for editing the temporary / local profile associated with
# a cardset.
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""This handles editing the local profile editor, (for temporary options)"""


from gi.repository import Gtk

from .SutekhDialog import SutekhDialog
from .AutoScrolledWindow import AutoScrolledWindow
from .PreferenceTable import PreferenceTable
from .BaseConfigFile import FRAME


class LocalProfileEditor(SutekhDialog):
    """Dialog which allows the user to set temporary option profiles.
       """
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # Gtk.Widget, so many public methods

    RESPONSE_CLOSE = 1
    RESPONSE_CANCEL = 2

    def __init__(self, oParent, oConfig, sFrame, sCardSet):
        super().__init__(
            "Edit Local Profile", oParent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)

        self.__oParent = oParent
        self.__oConfig = oConfig
        self.__sFrame = sFrame
        self.__sCardSet = sCardSet
        self.__dUnsavedChanges = None

        aOptions = []
        for sKey in self.__oConfig.profile_options(FRAME):
            if sKey == "name":
                continue
            aOptions.append((sKey, self.__oConfig.get_option_spec(FRAME, sKey),
                             True))

        self.__oOptionsTable = PreferenceTable(aOptions,
                                               oConfig.get_validator())
        self.vbox.pack_start(AutoScrolledWindow(self.__oOptionsTable),
                             True, True, 0)

        self.set_default_size(700, 550)
        self.connect("response", self._button_response)
        self.add_button("Cancel", self.RESPONSE_CANCEL)
        self.add_button("Close", self.RESPONSE_CLOSE)

        self.show_all()
        self._repopulate_options()

    def _button_response(self, _oWidget, iResponse):
        """Handle dialog response"""
        if iResponse != self.RESPONSE_CLOSE:
            self.destroy()
            return

        self._store_active_profile()
        if self._check_unsaved_changes():
            self._save_unsaved_changes()
            self.destroy()
        else:
            # Evil recursion
            self.destroy()
            oDlg = LocalProfileEditor(self.__oParent, self.__oConfig,
                                      self.__sFrame, self.__sCardSet)
            oDlg.run()

    def _repopulate_options(self):
        """Refresh the contents of the options box."""
        dNewValues = {}
        dInherited = {}
        sFrame, sCardSet = self.__sFrame, self.__sCardSet
        for sKey in self.__oConfig.profile_options(FRAME):
            dNewValues[sKey] = \
                self.__oConfig.get_local_frame_option(sFrame, sKey)
            dInherited[sKey] = self.__oConfig.get_deck_option(sFrame, sCardSet,
                                                              sKey,
                                                              bUseLocal=False)
        self.__oOptionsTable.update_values(dNewValues, {}, {}, dInherited)

    def _check_unsaved_changes(self):
        """Check that none of the changes make are bad.

        Return True if the changes are safe for saving, False otherwise.
        """
        # TODO: proper checks
        # TODO: proper complaints
        return True

    def _save_unsaved_changes(self):
        """Save all the unsaved changes."""
        sFrame = self.__sFrame
        for sKey, sValue in self.__dUnsavedChanges.items():
            self.__oConfig.set_local_frame_option(sFrame, sKey, sValue)

    def _store_active_profile(self):
        """Store the unsaved local profile changes."""
        self.__dUnsavedChanges = self.__oOptionsTable.get_values()
