# WriteArdbXML.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based off the Anarach Revolt Deck Builder xml support,
# ARDB (c) Francios Gombalt, Christoph Boget, Ville Virta and Vincent Ripoll
# GPL - see COPYING for details

"""
Give a list of Abstract Cards in a set, write a XML file compatable with
the Anarch Revolt Deck Builder
"""

from sutekh.core.SutekhObjects import IAbstractCard
from sutekh.SutekhInfo import SutekhInfo
from sutekh.SutekhUtility import pretty_xml
import time
try:
    from xml.etree.ElementTree import Element, SubElement, ElementTree
except ImportError:
    from elementtree.ElementTree import Element, SubElement, ElementTree

class WriteArdbXML(object):
    def gen_tree(self, sSetName, sAuthor, sDescription, dCards):
        """
        Creates the actual XML document into memory. Allows for conversion
        to HTML without using a Temporary file
        """
        oRoot = Element('deck')

        sDateWritten = time.strftime('%Y-%m-%d', time.localtime())
        oRoot.attrib['generator'] = "Sutekh [ %s ]" % SutekhInfo.VERSION_STR
        oRoot.attrib['formatVersion'] = "-TODO-1.0" # Claim same version as recent ARDB
        # Should this be an attribute of VersionTable?
        oRoot.attrib['databaseVersion'] = "Sutekh-20071201"
        oNameElem = SubElement(oRoot, 'name')
        oNameElem.text  = sSetName
        oAuthElem = SubElement(oRoot, 'author')
        oAuthElem.text = sAuthor
        oDescElem = SubElement(oRoot, 'description')
        oDescElem.text = sDescription
        oDateElem = SubElement(oRoot, 'date')
        oDateElem.text = sDateWritten

        (dVamps, iCryptSize, iMin, iMax, fAvg) = self.extract_crypt(dCards)
        (dLib, iLibSize) = self.extract_library(dCards)

        oCryptElem = SubElement(oRoot, 'crypt', size=str(iCryptSize),
                min=str(iMin), max=str(iMax), avg=str(fAvg))
        for tKey, iNum in dVamps.iteritems():
            iId, sName = tKey
            oCard = IAbstractCard(sName)
            oCardElem = SubElement(oCryptElem, 'vampire',
                    databaseID=str(iId), count=str(iNum))
            # This won't match the ARDB ID's, unless by chance.
            # It looks like that should not be an issue as ARDB will
            # use the name if the IDs don't match
            # It's unclear to me what values ARDB uses here, but
            # these are fine for the xml2html conversion, and look meaningful
            oAdvElem = SubElement(oCardElem, 'adv')
            oNameElem = SubElement(oCardElem, 'name')
            if oCard.level is not None:
                oAdvElem.text = '(Advanced)'
                # This is a bit hackish
                oNameElem.text = sName.replace(' (Advanced)', '')
            else:
                oNameElem.text = sName
            oDiscElem = SubElement(oCardElem, 'disciplines')
            sDisciplines = self.get_disciplines(oCard)
            oDiscElem.text = sDisciplines
            aClan = [x.name for x in oCard.clan]
            oClanElem = SubElement(oCardElem, 'clan')
            oCapElem = SubElement(oCardElem, 'capacity')
            if len(oCard.creed) > 0:
                # ARDB seems to treat all Imbued as being of the same clan
                # Should we do an Imbued:Creed thing?
                oClanElem.text = 'Imbued'
                oCapElem.text = str(oCard.life)
            else:
                oClanElem.text = aClan[0]
                oCapElem.text = str(oCard.capacity)
            oGrpElem = SubElement(oCardElem, 'group')
            oGrpElem.text = str(oCard.group)
            # ARDB doesn't handle sect specifically
            # No idea how ARDB represents independant titles -
            # this seems set when the ARDB database is created, and is
            # not in the ARDB codebase
            if len(oCard.title) > 0:
                oTitleElem = SubElement(oCardElem, 'title')
                aTitles = [oC.name for oC in oCard.title]
                oTitleElem.text = aTitles[0]
            oTextElem = SubElement(oCardElem, 'text')
            oTextElem.text = oCard.text

        oLibElem = SubElement(oRoot, 'library', size=str(iLibSize))
        for tKey, iNum in dLib.iteritems():
            iId, sName = tKey
            oCard = IAbstractCard(sName)
            oCardElem = SubElement(oLibElem, 'card', databaseID=str(iId),
                    count=str(iNum))
            oNameElem = SubElement(oCardElem, 'name')
            oNameElem.text = sName
            if oCard.costtype is not None:
                oCostElem = SubElement(oCardElem, 'cost')
                oCostElem.text = "%s %s " % (str(oCard.cost), oCard.costtype )
            if len(oCard.clan) > 0:
                # ARDB also strores things like "requires a prince"
                # we don't so too bad
                oReqElem = SubElement(oCardElem, 'requirement')
                aClan = [x.name for x in oCard.clan]
                oReqElem.text = "/".join(aClan)
            # Looks like it should be the right thing, but may not
            aTypes = [x.name for x in oCard.cardtype]
            oTypeElem = SubElement(oCardElem, 'type')
            oTypeElem.text = "/".join(aTypes)
            # Not sure if this does quite the right thing here
            sDisciplines = self.get_disciplines(oCard)
            if sDisciplines != '':
                oDiscElem = SubElement(oCardElem, 'disciplines')
                oDiscElem.text = sDisciplines
            oTextElem = SubElement(oCardElem, 'text')
            oTextElem.text = oCard.text
        return oRoot

    def write(self, fOut, sSetName, sAuthor, sDescription, dCards):
        """
        Takes filename, deck details and a dictionary of cards, of the form
        dCard[(id,name)]=count
        """
        oRoot = self.gen_tree(sSetName, sAuthor, sDescription, dCards)
        pretty_xml(oRoot)
        ElementTree(oRoot).write(fOut)

    def get_disciplines(self, oCard):
        aDisc = []
        aTypes = [x.name for x in oCard.cardtype]
        if aTypes[0] == 'Vampire':
            if not len(oCard.discipline) ==  0:
                for oDisc in oCard.discipline:
                    if oDisc.level == 'superior':
                        aDisc.append(oDisc.discipline.name.upper())
                    else:
                        aDisc.append(oDisc.discipline.name)
                aDisc.sort() # May not be needed
                return " ".join(aDisc)
            else:
                return ""
        elif aTypes[0] == 'Imbued':
            if not len(oCard.virtue) == 0:
                return " ".join([x.name for x in oCard.virtue])
            else:
                return ""
        else:
            # Dunno what we got, but we can't extract discipline'ish things from it
            return ""

    def extract_crypt(self, dCards):
        iCryptSize = 0
        iMax = 0
        iMin = 75
        fAvg = 0.0
        dVamps = {}
        for tKey, iCount in dCards.iteritems():
            iId, sName = tKey
            oCard = IAbstractCard(sName)
            aTypes = [x.name for x in oCard.cardtype]
            if aTypes[0] == 'Vampire':
                dVamps[tKey] = iCount
                iCryptSize += iCount
                fAvg += oCard.capacity*iCount
                if oCard.capacity > iMax:
                    iMax = oCard.capacity
                if oCard.capacity < iMin:
                    iMin = oCard.capacity
            if aTypes[0] == 'Imbued':
                dVamps[tKey] = iCount
                iCryptSize += iCount
                fAvg += oCard.life*iCount
                if oCard.capacity > iMax:
                    iMax = oCard.life
                if oCard.capacity < iMin:
                    iMin = oCard.life
        if iCryptSize > 0:
            fAvg = round(fAvg/iCryptSize, 2)
        if iMin == 75:
            iMin = 0
        return (dVamps, iCryptSize, iMin, iMax, fAvg)

    def extract_library(self, dCards):
        iSize = 0
        dLib = {}
        for tKey, iCount in dCards.iteritems():
            iId, sName = tKey
            oCard = IAbstractCard(sName)
            aTypes = [x.name for x in oCard.cardtype]
            if aTypes[0] != 'Vampire' and aTypes[0] != 'Imbued':
                dLib[tKey] = iCount
                iSize += iCount
        return (dLib, iSize)
