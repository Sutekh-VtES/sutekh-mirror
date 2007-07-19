# ConfigFile.py
# Config File handling object
# Wrapper around ConfigParser with some hooks for Sutekh purposes
# Copyright Neil Muller <drnlmuller+sutekh@gmail.com> 2007
# License: GPL. See COPYRIGHT file for details

from ConfigParser import RawConfigParser

class ConfigFile(object):

    __sFiltersSection = 'filters'
    __sGUISection = 'gui'

    def __init__(self,sFileName):
        self.__sFileName = sFileName
        self.__oConfig = RawConfigParser()
        # Use read to parse file if it exists
        self.__oConfig.read(self.__sFileName)

        if not self.__oConfig.has_section(self.__sGUISection):
            self.__oConfig.add_section(self.__sGUISection)

        if not self.__oConfig.has_section(self.__sFiltersSection):
            self.__oConfig.add_section(self.__sFiltersSection)

        self.__iNum = len(self.__oConfig.items(self.__sFiltersSection))

    def __str__(self):
        return "FileName : "+self.__sFileName

    def write(self):
        self.__oConfig.write(open(self.__sFileName,'w'))

    def getFilters(self):
        return [x[1] for x in self.__oConfig.items(self.__sFiltersSection)]

    def addFilter(self,sFilter):
        aOptions = self.__oConfig.options(self.__sFiltersSection)
        self.__iNum+=1
        sKey = 'user filter '+str(self.__iNum)
        while sKey in aOptions:
            self.__iNum+=1
            sKey = 'user filter '+str(self.__iNum)
        self.__oConfig.set(self.__sFiltersSection,sKey,sFilter)

    def removeFilter(self,sFilter):
        # We remove the first instance of the filter we find
        for sOption,sFilterinFile in self.__oConfig.items(self.__sFiltersSection):
            if sFilterinFile == sFilter:
                self.__oConfig.remove_option(self.__sFiltersSection,sOption)
                return


