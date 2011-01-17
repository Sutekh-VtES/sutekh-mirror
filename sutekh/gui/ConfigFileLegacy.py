# ConfigFileLegacy.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Legacy config file handling object
# Old config file was a wrapper around ConfigParser with some hooks for Sutekh
# purposes
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

"""Legacy config file reader for Sutekh"""

from ConfigParser import RawConfigParser, NoOptionError
from sutekh.gui.ConfigFile import ConfigFile


class ConfigFileLegacy(object):
    """Handle the setup and management of the old config file format.

       Ensure that the needed sections exist, and that sensible
       defaults values are assigned.
       """
    # pylint: disable-msg=R0904
    # We need to provide fine-grained access to all the data,
    # so lots of methods

    __sFiltersSection = 'Filters'
    __sPanesSection = 'Open Panes'
    __sPrefsSection = 'GUI Preferences'
    __sPluginsSection = 'Plugin Options'
    __sPaneInfoSection = 'Pane settings'

    def __init__(self, sFileName):
        self.__sFileName = sFileName
        self.__oConfig = RawConfigParser()
        # Use read to parse file if it exists
        self.__oConfig.read(self.__sFileName)

        if not self.__oConfig.has_section(self.__sPrefsSection):
            self.__oConfig.add_section(self.__sPrefsSection)
            # default to saving on exit
            self.set_save_on_exit(True)

        if 'save pane sizes' not in self.__oConfig.options(
                self.__sPrefsSection):
            self.set_save_precise_pos(True)

        if 'show zero count cards' not in self.__oConfig.options(
                self.__sPrefsSection):
            self.set_show_zero_count_cards(False)

        if 'save window size' not in self.__oConfig.options(
                self.__sPrefsSection):
            self.set_save_window_size(True)

        if 'postfix name display' not in self.__oConfig.options(
                self.__sPrefsSection):
            self.set_postfix_the_display(False)

        if not self.__oConfig.has_section(self.__sPanesSection):
            self.__oConfig.add_section(self.__sPanesSection)
            # No panes information, so we set 'sensible' defaults
            self.add_frame(1, 'physical_card', 'White Wolf Card List', False,
                    False, -1)
            self.add_frame(2, 'Card Text', 'Card Text', False, False, -1)
            self.add_frame(3, 'Card Set List', 'Card Set List', False, False,
                    -1)
            self.add_frame(4, 'physical_card_set', 'My Collection', False,
                    False, -1)

        if not self.__oConfig.has_section(self.__sFiltersSection):
            self.__oConfig.add_section(self.__sFiltersSection)

        self.__iNum = len(self.__oConfig.items(self.__sFiltersSection))

        if not self.__oConfig.has_section(self.__sPluginsSection):
            self.__oConfig.add_section(self.__sPluginsSection)

        if not self.__oConfig.has_section(self.__sPaneInfoSection):
            self.__oConfig.add_section(self.__sPaneInfoSection)

    def _get_bool_key(self, sSection, sKey):
        """Test if a boolean key is set or not"""
        return self.__oConfig.get(sSection, sKey) == 'yes'

    def _set_bool_key(self, sSection, sKey, bValue):
        """Set a boolean key"""
        if bValue:
            self.__oConfig.set(sSection, sKey, 'yes')
        else:
            self.__oConfig.set(sSection, sKey, 'no')

    # pylint: disable-msg=R0201
    # method for backwards compatibility
    def write(self):
        """Write the config file to disk."""
        raise RuntimeError("Writing the old config file no longer supported")

    # pylint: enable-msg=R0201

    def convert(self, sFilename):
        """Return a new-style Sutekh config object."""
        # pylint: disable-msg=R0914
        # Need to convert a lot of options, so we need many variables
        oConfig = ConfigFile(sFilename)
        oConfig.validate()

        # Global Options

        for fSetter, fGetter in (
            (oConfig.set_database_uri, self.get_database_uri),
            (oConfig.set_icon_path, self.get_icon_path),
            (oConfig.set_postfix_the_display, self.get_postfix_the_display),
            (oConfig.set_save_on_exit, self.get_save_on_exit),
            (oConfig.set_save_precise_pos, self.get_save_precise_pos),
            (oConfig.set_save_window_size, self.get_save_window_size),
            (oConfig.set_window_size, self.get_window_size),
            ):
            oValue = fGetter()
            if oValue is not None:
                fSetter(oValue)

        # Open Frames

        oConfig.clear_open_frames()
        for iPaneNumber, sType, sName, bVertical, bClosed, iPos in \
            self.get_all_panes():
            oConfig.add_frame(iPaneNumber, sType, sName, bVertical, bClosed,
                    iPos, None)

        # Filters

        for sKey, sFilter in self.get_filter_keys():
            oConfig.add_filter(sKey, sFilter)

        # Deck Options
        # Note: deck options from .get_all_pane_info() and
        # .get_show_zero_count_cards(). This would require constructing
        # profiles and associating them with frames automatically which is
        # unlikely to create something the user is happy with. The cost of
        # reconfiguring these options should be fairly low.

        # Global Plugin Options

        dKey2PluginMap = {
            'card image path': 'CardImagePlugin',
            'HTML export mode': 'CardSetExportHTML',
            'show starters': 'StarterInfoPlugin',
        }

        for sKey in self.__oConfig.options(self.__sPluginsSection):
            if sKey not in dKey2PluginMap:
                # skip keys that aren't known are are presumablly garbage
                continue
            sPlugin = dKey2PluginMap[sKey]
            sValue = self.get_plugin_key(sKey)
            oConfig.set_plugin_key(sPlugin, sKey, sValue, bCreateSection=True)

        return oConfig

    def pre_save_clear(self):
        """Clear out old saved pos, before saving new stuff"""
        aKeys = self.__oConfig.options(self.__sPanesSection)
        for sKey in aKeys:
            self.__oConfig.remove_option(self.__sPanesSection, sKey)
        aKeys = self.__oConfig.options(self.__sPaneInfoSection)
        for sKey in aKeys:
            self.__oConfig.remove_option(self.__sPaneInfoSection, sKey)

    def get_all_panes(self):
        """Get the all the panes saved in the config file, and their
           positions."""
        aRes = []
        for sKey, sValue in self.__oConfig.items(self.__sPanesSection):
            if not sKey.startswith('pane'):
                # invalid key
                continue
            try:
                iPaneNumber = int(sKey.split(' ')[1])
            except ValueError:
                # invalid key
                continue
            # Type is before 1st colon in the name
            if sValue.find(':') == -1:
                # invalid format, so skip
                continue
            sData, sName = sValue.split(':', 1)
            aData = sData.split('.')
            sType = aData[0]
            sPos = '-1'
            bVertical = False
            bClosed = False
            if len(aData) > 1:
                if aData[1] == 'V':
                    bVertical = True
                    if len(aData) > 2:
                        sPos = aData[2]
                elif aData[1] == 'C':
                    bClosed = True
                    # We aim for minimal impact on the layout of other panes
                    sPos = '0'
                else:
                    sPos = aData[1]
            try:
                iPos = int(sPos)
            except ValueError:
                iPos = -1
            aRes.append((iPaneNumber, sType, sName, bVertical, bClosed, iPos))
        aRes.sort()  # Numbers denote ordering
        return aRes

    def get_all_pane_info(self):
        """Get the pane info (card mode, etc) saved in the config file"""
        dRes = {}
        for tPaneInfo in self.__oConfig.items(self.__sPaneInfoSection):
            # Format is 'pane number' =
            #        Extra Level Mode:Parent Count Mode:Card Mode:Name
            # We can' use the name as a key, since the key isn't case sensitive
            try:
                sExtraLevelMode, sParentCount, sShowCardMode, sName = \
                        tPaneInfo[1].split(':', 3)
                dRes[sName] = (int(sExtraLevelMode), int(sParentCount),
                        int(sShowCardMode))
            except ValueError:
                # skip this one then
                continue
        return dRes

    def get_postfix_the_display(self):
        """Query the 'postfix names' option."""
        return self._get_bool_key(self.__sPrefsSection, 'postfix name display')

    def set_postfix_the_display(self, bPostfix):
        """Set the 'postfix names' option."""
        self._set_bool_key(self.__sPrefsSection, 'postfix name display',
                bPostfix)

    def get_save_on_exit(self):
        """Query the 'save on exit' option."""
        return self._get_bool_key(self.__sPrefsSection, 'save on exit')

    def set_save_on_exit(self, bSaveOnExit):
        """Set the 'save on exit' option."""
        self._set_bool_key(self.__sPrefsSection, 'save on exit', bSaveOnExit)

    def get_save_precise_pos(self):
        """Query the 'save pane sizes' option."""
        return self._get_bool_key(self.__sPrefsSection, 'save pane sizes')

    def set_save_precise_pos(self, bSavePos):
        """Set the 'save pane sizes' option."""
        self._set_bool_key(self.__sPrefsSection, 'save pane sizes', bSavePos)

    def get_save_window_size(self):
        """Query the 'save window size' option."""
        return self._get_bool_key(self.__sPrefsSection, 'save window size')

    def set_save_window_size(self, bSavePos):
        """Set the 'save window size' option."""
        self._set_bool_key(self.__sPrefsSection, 'save window size', bSavePos)

    def get_show_zero_count_cards(self):
        """Query the 'show zero count cards' option."""
        return self._get_bool_key(self.__sPrefsSection,
                'show zero count cards')

    def set_show_zero_count_cards(self, bShowZero):
        """Set the 'show zero count cards' option."""
        self._set_bool_key(self.__sPrefsSection, 'show zero count cards',
                bShowZero)

    # pylint: disable-msg=R0913
    # We need all the info in the arguments here
    def add_frame(self, iFrameNumber, sType, sName, bVertical, bClosed, iPos):
        """Add a frame with the given position info to the config file"""
        sKey = 'pane %d' % iFrameNumber
        sData = sType
        if bVertical:
            sData += '.V'
        elif bClosed:
            sData += '.C'
        if iPos > 0 and self.get_save_precise_pos() and not bClosed:
            sData += '.%d' % iPos
        sValue = '%s:%s' % (sData, sName)
        self.__oConfig.set(self.__sPanesSection, sKey, sValue)

    # pylint: enable-msg=R0913

    def add_pane_info(self, iFrameNumber, sName, tInfo):
        """Save the pane info"""
        sKey = 'pane %d' % iFrameNumber
        iExtraLevelMode, iParentCount, iShowCardMode = tInfo
        sValue = '%d:%d:%d:%s' % (iExtraLevelMode, iParentCount, iShowCardMode,
                sName)
        self.__oConfig.set(self.__sPaneInfoSection, sKey, sValue)

    def set_database_uri(self, sDatabaseURI):
        """Set the configured database URI"""
        self.__oConfig.set(self.__sPrefsSection, "database url", sDatabaseURI)

    def get_database_uri(self):
        """Get database URI from the config file"""
        try:
            sResult = self.__oConfig.get(self.__sPrefsSection, "database url")
        except NoOptionError:
            sResult = None
        return sResult

    def get_icon_path(self):
        """Get the icon path from the config file"""
        try:
            sResult = self.__oConfig.get(self.__sPrefsSection, "icon path")
        except NoOptionError:
            sResult = None
        return sResult

    def set_icon_path(self, sPath):
        """Set the configured icon path"""
        self.__oConfig.set(self.__sPrefsSection, "icon path", sPath)

    def get_window_size(self):
        """Get the saved window size from the config file."""
        try:
            sResult = self.__oConfig.get(self.__sPrefsSection, 'window size')
            iWidth, iHeight = [int(x) for x in sResult.split(',')]
        except NoOptionError:
            iWidth, iHeight = -1, -1
        return iWidth, iHeight

    def save_window_size(self, tSize):
        """Save the current window size."""
        sPos = '%d, %d' % (tSize[0], tSize[1])
        self.__oConfig.set(self.__sPrefsSection, 'window size', sPos)

    # filters section

    def get_filters(self):
        """Get all the filters in the config file."""
        return [x[1] for x in self.__oConfig.items(self.__sFiltersSection)]

    def get_filter_keys(self):
        """Get the keys used to reference the filters."""
        return self.__oConfig.items(self.__sFiltersSection)

    def get_filter(self, sKey):
        """Return the filter associated with the given key or None."""
        if sKey.lower() in self.__oConfig.options(self.__sFiltersSection):
            return self.__oConfig.get(self.__sFiltersSection, sKey)
        else:
            return None

    def add_filter(self, sKey, sFilter):
        """Add a filter to the config file."""
        if sKey.lower() not in self.__oConfig.options(self.__sFiltersSection):
            self.__oConfig.set(self.__sFiltersSection, sKey, sFilter)

    def remove_filter(self, sKey, sFilter):
        """Remove a filter from the file"""
        # Make sure Filer and key match
        if sKey.lower() in self.__oConfig.options(self.__sFiltersSection) and \
                sFilter == self.__oConfig.get(self.__sFiltersSection, sKey):
            self.__oConfig.remove_option(self.__sFiltersSection, sKey)

    def replace_filter(self, sKey, sOldFilter, sNewFilter):
        """Replace a filter in the file with new filter"""
        if sKey.lower() in self.__oConfig.options(self.__sFiltersSection) and \
                sOldFilter == self.__oConfig.get(self.__sFiltersSection, sKey):
            self.__oConfig.remove_option(self.__sFiltersSection, sKey)
            self.__oConfig.set(self.__sFiltersSection, sKey, sNewFilter)

    # plugins section

    def get_plugin_key(self, sKey):
        """Get an option from the plugins section.

           Return None if no option is set
           """
        try:
            sResult = self.__oConfig.get(self.__sPluginsSection, sKey)
        except NoOptionError:
            sResult = None
        return sResult

    def set_plugin_key(self, sKey, sValue):
        """Set a value in the plugin section"""
        self.__oConfig.set(self.__sPluginsSection, sKey, sValue)
