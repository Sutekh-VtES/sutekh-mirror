# ConfigFile.py
# Config File handling object
# Wrapper around ConfigParser with some hooks for Sutekh purposes
# Copyright Neil Muller <drnlmuller+sutekh@gmail.com> 2007
# License: GPL. See COPYRIGHT file for details

from ConfigParser import RawConfigParser

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

        if not self.__oConfig.has_section(self.__sPanesSection):
            self.__oConfig.add_section(self.__sPanesSection)
            # No panes information, so we set 'sensible' defaults
            self.addPane(1, 'abstract_card', 'Abstract Cards')
            self.addPane(2, 'physical_card', 'Physical Cards')
            self.addPane(3, 'Card Text', 'Card Text')

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
            sType, sName = sValue.split(':', 1)
            aRes.append((iPaneNumber, sType, sName))
        aRes.sort() # Numbers denote ordering
        return aRes

    def getSaveOnExit(self):
        return self.__oConfig.get(self.__sPrefsSection, 'save on exit') == 'yes'

    def setSaveOnExit(self, bSaveOnExit):
        if bSaveOnExit:
            self.__oConfig.set(self.__sPrefsSection, 'save on exit', 'yes')
        else:
            self.__oConfig.set(self.__sPrefsSection, 'save on exit', 'no')

    def addPane(self, iPaneNumber, sType, sName):
        aOptions = self.__oConfig.options(self.__sPanesSection)
        sKey = 'pane ' + str(iPaneNumber)
        sValue = sType + ':' + sName
        self.__oConfig.set(self.__sPanesSection, sKey, sValue)

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




