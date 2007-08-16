# ConfigFile.py
# Config File handling object
# Wrapper around ConfigParser with some hooks for Sutekh purposes
# Copyright Neil Muller <drnlmuller+sutekh@gmail.com> 2007
# License: GPL. See COPYRIGHT file for details

from ConfigParser import RawConfigParser

class ConfigFileListener(object):
    """Listener object for config changes - inspired by CardListModeListener"""

    def addFilter(self,sFilter):
        """New Filter added"""
        pass

    def removeFilter(self,sFilter):
        """Filter removed"""
        pass

class ConfigFile(object):

    __sFiltersSection = 'filters'
    __sWinPosSection = 'Window Pos'
    __sWinNameSection = 'Window Name'
    __sCardSetsSection = 'Card Sets'
    __sPrefsSection = 'GUI Preferences'

    def __init__(self,sFileName):
        self.__sFileName = sFileName
        self.__oConfig = RawConfigParser()
        # Use read to parse file if it exists
        self.__oConfig.read(self.__sFileName)
        self.__dListeners = {}

        if not self.__oConfig.has_section(self.__sPrefsSection):
            self.__oConfig.add_section(self.__sPrefsSection)
            # default to saving on exit
            self.setSaveOnExit(True)

        if not self.__oConfig.has_section(self.__sCardSetsSection):
            self.__oConfig.add_section(self.__sCardSetsSection)

        if not self.__oConfig.has_section(self.__sWinPosSection):
            self.__oConfig.add_section(self.__sWinPosSection)

        if not self.__oConfig.has_section(self.__sWinNameSection):
            self.__oConfig.add_section(self.__sWinNameSection)

        if not self.__oConfig.has_section(self.__sFiltersSection):
            self.__oConfig.add_section(self.__sFiltersSection)

        self.__iNum = len(self.__oConfig.items(self.__sFiltersSection))

    def __str__(self):
        return "FileName : " + self.__sFileName

    def addListener(self,oListener):
        self.__dListeners[oListener] = None

    def removeListener(self,oListener):
        del self.__dListenders[oListener]

    def write(self):
        self.__oConfig.write(open(self.__sFileName,'w'))

    def getFilters(self):
        return [x[1] for x in self.__oConfig.items(self.__sFiltersSection)]

    def getWinPos(self,sTitle):
        for sKey,sName in self.__oConfig.items(self.__sWinNameSection):
            if sName == sTitle:
                sPos = self.__oConfig.get(self.__sWinPosSection,sKey)
                X,Y = sPos.split(',')
                return ( int(X), int(Y) )
        return None

    def preSaveClear(self):
        """Clear out old saved pos, before saving new stuff"""
        aKeys = self.__oConfig.options(self.__sWinPosSection)
        for sKey in aKeys:
            self.__oConfig.remove_option(self.__sWinPosSection,sKey)
        aKeys = self.__oConfig.options(self.__sWinNameSection)
        for sKey in aKeys:
            self.__oConfig.remove_option(self.__sWinNameSection,sKey)
        aKeys = self.__oConfig.options(self.__sCardSetsSection)
        for sKey in aKeys:
            self.__oConfig.remove_option(self.__sCardSetsSection,sKey)

    def getAllWinPos(self):
        aRes = []
        for sKey,sName in self.__oConfig.items(self.__sWinNameSection):
            sPos = self.__oConfig.get(self.__sWinPosSection,sKey)
            X,Y = sPos.split(',')
            aRes.append( ( sName, int(X), int(Y) ) )
        return aRes

    def getSaveOnExit(self):
        return self.__oConfig.get(self.__sPrefsSection,'save on exit') == 'yes'

    def setSaveOnExit(self,bSaveOnExit):
        if bSaveOnExit:
            self.__oConfig.set(self.__sPrefsSection,'save on exit','yes')
        else:
            self.__oConfig.set(self.__sPrefsSection,'save on exit','no')

    def getCardSets(self):
        # Type is before 1st colon in the saved name
        return [(x[1].split(':',1)) for x in self.__oConfig.items(self.__sCardSetsSection)]

    def addWinPos(self,sWindowTitle,tPos):
        sPos = str(tPos[0]) + ',' + str(tPos[1])
        aOptions = self.__oConfig.options(self.__sWinPosSection)
        iNum = len(aOptions)
        sKey = 'window ' + str(iNum)
        while sKey in aOptions:
            iNum += 1
            sKey = 'window ' + str(iNum)
        self.__oConfig.set(self.__sWinPosSection,sKey,sPos)
        self.__oConfig.set(self.__sWinNameSection,sKey,sWindowTitle)

    def addCardSet(self,sType,sCardSet):
        aOptions = self.__oConfig.options(self.__sCardSetsSection)
        iNum = len(aOptions)
        sKey = 'card set ' + str(iNum)
        while sKey in aOptions:
            iNum += 1
            sKey = 'card set ' + str(iNum)
        self.__oConfig.set(self.__sCardSetsSection,sKey,sType + ':' + sCardSet)

    def addFilter(self,sFilter):
        aOptions = self.__oConfig.options(self.__sFiltersSection)
        self.__iNum += 1
        sKey = 'user filter ' + str(self.__iNum)
        while sKey in aOptions:
            self.__iNum += 1
            sKey = 'user filter ' + str(self.__iNum)
        self.__oConfig.set(self.__sFiltersSection,sKey,sFilter)
        for oListener in self.__dListeners:
            oListener.addFilter(sFilter)

    def removeFilter(self,sFilter):
        # We remove the first instance of the filter we find
        for sOption,sFilterinFile in self.__oConfig.items(self.__sFiltersSection):
            if sFilterinFile == sFilter:
                self.__oConfig.remove_option(self.__sFiltersSection,sOption)
                for oListener in self.__dListeners:
                    oListener.removeFilter(sFilter)
                return


