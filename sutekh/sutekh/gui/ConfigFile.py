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

    def addFilter(self, sFilter, sKey):
        """New Filter added"""
        pass

    def removeFilter(self, sFilter, sKey):
        """Filter removed"""
        pass

    def replaceFilter(self, sOldFilter, sNewFilter, sKey):
        """A Filter has been replaced"""
        pass

class ConfigFile(object):

    __sFiltersSection = 'Filters'
    __sPanesSection = 'Open Panes'
    __sPrefsSection = 'GUI Preferences'

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

        if not self.__oConfig.has_section(self.__sPanesSection):
            self.__oConfig.add_section(self.__sPanesSection)
            # No panes information, so we set 'sensible' defaults
            self.add_frame(1, 'abstract_card', 'Abstract Cards', False, -1)
            self.add_frame(2, 'physical_card', 'Physical Cards', False, -1)
            self.add_frame(3, 'Card Text', 'Card Text', False, -1)

        if not self.__oConfig.has_section(self.__sFiltersSection):
            self.__oConfig.add_section(self.__sFiltersSection)

        self.__iNum = len(self.__oConfig.items(self.__sFiltersSection))

    def __str__(self):
        return "FileName : " + self.__sFileName

    def addListener(self, oListener):
        self.__dListeners[oListener] = None

    def removeListener(self, oListener):
        del self.__dListenders[oListener]

    def write(self):
        self.__oConfig.write(open(self.__sFileName, 'w'))

    def getFilters(self):
        return [x[1] for x in self.__oConfig.items(self.__sFiltersSection)]

    def getFiltersKeys(self):
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
        return self.__oConfig.get(self.__sPrefsSection, 'save on exit') == 'yes'

    def setSaveOnExit(self, bSaveOnExit):
        if bSaveOnExit:
            self.__oConfig.set(self.__sPrefsSection, 'save on exit', 'yes')
        else:
            self.__oConfig.set(self.__sPrefsSection, 'save on exit', 'no')

    def get_save_precise_pos(self):
        return self.__oConfig.get(self.__sPrefsSection, 'save pane sizes') == 'yes'

    def set_save_precise_pos(self, bSavePos):
        if bSavePos:
            self.__oConfig.set(self.__sPrefsSection, 'save pane sizes', 'yes')
        else:
            self.__oConfig.set(self.__sPrefsSection, 'save pane sizes', 'no')

    def get_show_zero_count_cards(self):
        return self.__oConfig.get(self.__sPrefsSection, 'show zero count cards') == 'yes'

    def set_show_zero_count_cards(self, bShowZero):
        if bShowZero:
            self.__oConfig.set(self.__sPrefsSection, 'show zero count cards', 'yes')
        else:
            self.__oConfig.set(self.__sPrefsSection, 'show zero count cards', 'no')

    def add_frame(self, iFrameNumber, sType, sName, bVertical, iPos):
        aOptions = self.__oConfig.options(self.__sPanesSection)
        sKey = 'pane ' + str(iFrameNumber)
        sData = sType
        if bVertical:
            sData += '.V'
        if iPos > 0 and self.get_save_precise_pos():
            sData += '.' + str(iPos)
        sValue = sData + ':' + sName
        self.__oConfig.set(self.__sPanesSection, sKey, sValue)

    def set_databaseURI(self, sDatabaseURI):
        self.__oConfig.set(self.__sPrefsSection, "database url", sDatabaseURI)

    def get_databaseURI(self):
        try:
            sResult = self.__oConfig.get(self.__sPrefsSection, "database url")
        except NoOptionError:
            sResult = None
        return sResult

    def addFilter(self, sFilter):
        aOptions = self.__oConfig.options(self.__sFiltersSection)
        self.__iNum += 1
        sKey = 'user filter ' + str(self.__iNum)
        while sKey in aOptions:
            self.__iNum += 1
            sKey = 'user filter ' + str(self.__iNum)
        self.__oConfig.set(self.__sFiltersSection, sKey, sFilter)
        for oListener in self.__dListeners:
            oListener.addFilter(sFilter, sKey)

    def removeFilter(self, sFilter, sKey):
        # Make sure Filer and key match
        if sKey in self.__oConfig.options(self.__sFiltersSection) and \
                sFilter == self.__oConfig.get(self.__sFiltersSection, sKey):
            self.__oConfig.remove_option(self.__sFiltersSection, sKey)
            for oListener in self.__dListeners:
                oListener.removeFilter(sFilter, sKey)
            return

    def replaceFilter(self, sOldFilter, sNewFilter, sKey):
        if sKey in self.__oConfig.options(self.__sFiltersSection) and \
                sOldFilter == self.__oConfig.get(self.__sFiltersSection, sKey):
            self.__oConfig.remove_option(self.__sFiltersSection, sKey)
            self.__oConfig.set(self.__sFiltersSection, sKey, sNewFilter)
            for oListener in self.__dListeners:
                oListener.replaceFilter(sOldFilter, sNewFilter, sKey)
            return




