# WriteArdbXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based off the Anarach Revolt Deck Builder xml support,
# ARDB (c) Francios Gombalt, Christoph Boget, Ville Virta and Vincent Ripoll
# GPL - see COPYING for details

"""Given a list of Abstract Cards in a set, write a XML file compatable with
   the Anarch Revolt Deck Builder."""

from sutekh.core.SutekhObjects import IAbstractCard
from sutekh.core.ArdbInfo import ArdbInfo, escape_ardb_name
from sutekh.SutekhUtility import pretty_xml
import time
# pylint: disable-msg=E0611, F0401
# xml.etree is a python2.5 thing
try:
    from xml.etree.ElementTree import Element, SubElement, ElementTree, \
            tostring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, ElementTree, \
            tostring
# pylint: enable-msg=E0611, F0401


class WriteArdbXML(ArdbInfo):
    """Reformat cardset to elementTree and export it to a ARDB
       compatible XML file."""

    def gen_tree(self, sSetName, sAuthor, sDescription, dCards):
        """Creates the actual XML document into memory."""
        # pylint: disable-msg=R0914
        # Need this many local variables to create proper XML tree
        oRoot = Element('deck')

        sDateWritten = time.strftime('%Y-%m-%d', time.localtime())
        oRoot.attrib['generator'] = "Sutekh [ %s ]" % self.sVersionString
        oRoot.attrib['formatVersion'] = self.sFormatVersion
        oRoot.attrib['databaseVersion'] = self.sDatabaseVersion
        oNameElem = SubElement(oRoot, 'name')
        oNameElem.text  = sSetName
        oAuthElem = SubElement(oRoot, 'author')
        oAuthElem.text = sAuthor
        oDescElem = SubElement(oRoot, 'description')
        oDescElem.text = sDescription
        oDateElem = SubElement(oRoot, 'date')
        oDateElem.text = sDateWritten

        dVamps, dCryptStats = self._extract_crypt(dCards)
        (dLib, iLibSize) = self._extract_library(dCards)

        oCryptElem = SubElement(oRoot, 'crypt', size=str(dCryptStats['size']),
                min=str(dCryptStats['min']), max=str(dCryptStats['max']),
                avg='%.2f' % dCryptStats['avg'])
        self.format_vamps(oCryptElem, dVamps)

        oLibElem = SubElement(oRoot, 'library', size=str(iLibSize))
        self.format_library(oLibElem, dLib)

        pretty_xml(oRoot)
        return oRoot

    def format_vamps(self, oCryptElem, dVamps):
        """Convert the Vampire dictionary into elementtree representation."""
        # pylint: disable-msg=R0914
        # Need this many local variables to create proper XML tree
        for tKey in sorted(dVamps, key = lambda x: x[1]):
            iNum = dVamps[tKey]
            iId, sName, sSet = tKey
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
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
            sName = escape_ardb_name(sName)
            if oCard.level is not None:
                oAdvElem.text = '(Advanced)'
                # This is a bit hackish
                oNameElem.text = sName.replace(' (Advanced)', '')
            else:
                oNameElem.text = sName
            oSetElem = SubElement(oCardElem, 'set')
            oSetElem.text = sSet
            oDiscElem = SubElement(oCardElem, 'disciplines')
            sDisciplines = self._gen_disciplines(oCard)
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

    def format_library(self, oLibElem, dLib):
        """Format the dictionary of library cards for the element tree."""
        # pylint: disable-msg=R0914
        # Need this many local variables to create proper XML tree
        for tKey in sorted(dLib, key = lambda x: x[1]):
            iNum = dLib[tKey]
            iId, sName, sTypeString, sSet = tKey
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            sName = escape_ardb_name(sName)
            oCardElem = SubElement(oLibElem, 'card', databaseID=str(iId),
                    count=str(iNum))
            oNameElem = SubElement(oCardElem, 'name')
            oNameElem.text = sName
            oSetElem = SubElement(oCardElem, 'set')
            oSetElem.text = sSet
            if oCard.costtype is not None:
                oCostElem = SubElement(oCardElem, 'cost')
                oCostElem.text = "%d %s " % (oCard.cost, oCard.costtype )
            if len(oCard.clan) > 0:
                # ARDB also strores things like "requires a prince"
                # we don't so too bad
                oReqElem = SubElement(oCardElem, 'requirement')
                aClan = [x.name for x in oCard.clan]
                oReqElem.text = "/".join(aClan)
            oTypeElem = SubElement(oCardElem, 'type')
            oTypeElem.text = sTypeString
            # Not sure if this does quite the right thing here
            sDisciplines = self._gen_disciplines(oCard)
            if sDisciplines != '':
                oDiscElem = SubElement(oCardElem, 'disciplines')
                oDiscElem.text = sDisciplines
            oTextElem = SubElement(oCardElem, 'text')
            oTextElem.text = oCard.text

    # pylint: disable-msg=R0913
    # we need all these arguments
    def write(self, fOut, sSetName, sAuthor, sDescription, oCardIter):
        """Takes filename, deck details and a dictionary of cards, of the
           form dCard[(id,name)] = count and writes the file."""
        dCards = self._get_cards(oCardIter)
        oRoot = self.gen_tree(sSetName, sAuthor, sDescription, dCards)
        ElementTree(oRoot).write(fOut)

    # pylint: enable-msg=R0913

    def gen_xml_string(self, sSetName, sAuthor, sDescription, oCardIter):
        """Generate string XML representation"""
        dCards = self._get_cards(oCardIter)
        oRoot = self.gen_tree(sSetName, sAuthor, sDescription, dCards)
        return tostring(oRoot)


