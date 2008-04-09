# ConfigFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Config File handling object
# Wrapper around ConfigParser with some hooks for Sutekh purposes
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

from ConfigParser import RawConfigParser, NoOptionError

class ConfigFileListener(object):
    """Listener object for config changes - inspired by CardListModeListener"""

    def add_filter(self, sFilter, sKey):
        """New Filter added"""
        pass

    def remove_filter(self, sFilter, sKey):
        """Filter removed"""
        pass

    def replace_filter(self, sOldFilter, sNewFilter, sKey):
        """A Filter has been replaced"""
        pass

class ConfigFile(object):

    __sFiltersSection = 'Filters'
    __sPanesSection = 'Open Panes'
    __sPrefsSection = 'GUI Preferences'
    __sPluginsSection = 'Plugin Options'

    def __init__(self, sFileName):
        self.__sFileName = sFileName
        self.__oConfig = RawConfigParser()
        # Use read to parse file if it exists
        self.__oConfig.read(self.__sFileName)
        self.__dListeners = {}

        if not self.__oConfig.has_section(self.__sPrefsSection):
            self.__oConfig.add_section(self.__sPrefsSection)
            # default to saving on exit
            self.setSaveOnExit(True)

        if 'save pane sizes' not in self.__oConfig.options(self.__sPrefsSection):
            self.set_save_precise_pos(True)

        if 'show zero count cards' not in self.__oConfig.options(self.__sPrefsSection):
            self.set_show_zero_count_cards(False)

        if 'save window size' not in self.__oConfig.options(self.__sPrefsSection):
            self.set_save_window_size(True)

        if not self.__oConfig.has_section(self.__sPanesSection):
            self.__oConfig.add_section(self.__sPanesSection)
            # No panes information, so we set 'sensible' defaults
            self.add_frame(1, 'abstract_card', 'Abstract Cards', False, -1)
            self.add_frame(2, 'physical_card', 'Physical Cards', False, -1)
            self.add_frame(3, 'Card Text', 'Card Text', False, -1)

        if not self.__oConfig.has_section(self.__sFiltersSection):
            self.__oConfig.add_section(self.__sFiltersSection)

        self.__iNum = len(self.__oConfig.items(self.__sFiltersSection))

        if not self.__oConfig.has_section(self.__sPluginsSection):
            self.__oConfig.add_section(self.__sPluginsSection)

    def __str__(self):
        return "FileName : " + self.__sFileName

    def _get_bool_key(self, sSection, sKey):
        """Test if a boolean key is set or not"""
        return self.__oConfig.get(sSection, sKey) == 'yes'


    def _set_bool_key(self, sSection, sKey, bValue):
        """Set a boolean key"""
        if bValue:
            self.__oConfig.set(sSection, sKey, 'yes')
        else:
            self.__oConfig.set(sSection, sKey, 'no')

    def add_listener(self, oListener):
        self.__dListeners[oListener] = None

    def remove_listener(self, oListener):
        del self.__dListeners[oListener]

    def write(self):
        self.__oConfig.write(open(self.__sFileName, 'w'))

    def get_filters(self):
        return [x[1] for x in self.__oConfig.items(self.__sFiltersSection)]

    def get_filter_keys(self):
        return self.__oConfig.items(self.__sFiltersSection)

    def preSaveClear(self):
        """Clear out old saved pos, before saving new stuff"""
        aKeys = self.__oConfig.options(self.__sPanesSection)
        for sKey in aKeys:
            self.__oConfig.remove_option(self.__sPanesSection, sKey)

    def getAllPanes(self):
        aRes = []
        for sKey, sValue in self.__oConfig.items(self.__sPanesSection):
            iPaneNumber = int(sKey.split(' ')[1])
            # Type is before 1st colon in the name
            sData, sName = sValue.split(':', 1)
            aData = sData.split('.')
            sType = aData[0]
            sPos = '-1'
            bVertical = False
            if len(aData) > 1:
                if aData[1] == 'V':
                    bVertical = True
                    if len(aData) > 2: sPos = aData[2]
                else:
                    sPos = aData[1]
            try:
                iPos = int(sPos)
            except ValueError:
                iPos = -1
            aRes.append((iPaneNumber, sType, sName, bVertical, iPos))
        aRes.sort() # Numbers denote ordering
        return aRes

    def getSaveOnExit(self):
        """Query the 'save on exit' option."""
        return self._get_bool_key(self.__sPrefsSection, 'save on exit')

    def setSaveOnExit(self, bSaveOnExit):
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

    def add_frame(self, iFrameNumber, sType, sName, bVertical, iPos):
        """Add a frame to the config file"""
        sKey = 'pane ' + str(iFrameNumber)
        sData = sType
        if bVertical:
            sData += '.V'
        if iPos > 0 and self.get_save_precise_pos():
            sData += '.' + str(iPos)
        sValue = sData + ':' + sName
        self.__oConfig.set(self.__sPanesSection, sKey, sValue)

    def set_databaseURI(self, sDatabaseURI):
        """Set the configured database URI"""
        self.__oConfig.set(self.__sPrefsSection, "database url", sDatabaseURI)

    def get_databaseURI(self):
        """Get database URI from the config file"""
        try:
            sResult = self.__oConfig.get(self.__sPrefsSection, "database url")
        except NoOptionError:
            sResult = None
        return sResult

    def get_window_size(self):
        try:
            sResult = self.__oConfig.get(self.__sPrefsSection, 'window size')
            iX, iY = [int(x) for x in sResult.split(',')]
        except NoOptionError:
            iX, iY = -1, -1
        return iX, iY

    def save_window_size(self, tSize):
        sPos = '%d, %d' % (tSize[0], tSize[1])
        self.__oConfig.set(self.__sPrefsSection, 'window size', sPos)

    def add_filter(self, sFilter):
        """Add a filter to the file, handling automatic numbering"""
        aOptions = self.__oConfig.options(self.__sFiltersSection)
        self.__iNum += 1
        sKey = 'user filter ' + str(self.__iNum)
        while sKey in aOptions:
            self.__iNum += 1
            sKey = 'user filter ' + str(self.__iNum)
        self.__oConfig.set(self.__sFiltersSection, sKey, sFilter)
        for oListener in self.__dListeners:
            oListener.add_filter(sFilter, sKey)

    def remove_filter(self, sFilter, sKey):
        """Remove a filter from the file"""
        # Make sure Filer and key match
        if sKey in self.__oConfig.options(self.__sFiltersSection) and \
                sFilter == self.__oConfig.get(self.__sFiltersSection, sKey):
            self.__oConfig.remove_option(self.__sFiltersSection, sKey)
            for oListener in self.__dListeners:
                oListener.remove_filter(sFilter, sKey)
            return

    def replace_filter(self, sOldFilter, sNewFilter, sKey):
        """Replace a filter in the file with new filter"""
        if sKey in self.__oConfig.options(self.__sFiltersSection) and \
                sOldFilter == self.__oConfig.get(self.__sFiltersSection, sKey):
            self.__oConfig.remove_option(self.__sFiltersSection, sKey)
            self.__oConfig.set(self.__sFiltersSection, sKey, sNewFilter)
            for oListener in self.__dListeners:
                oListener.replace_filter(sOldFilter, sNewFilter, sKey)
            return

    def get_plugin_key(self, sKey):
        """
        Get an option from the plugins section.
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
