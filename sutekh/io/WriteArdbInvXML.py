# WriteArdbInvXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based off the Anarach Revolt Deck Builder xml support,
# ARDB (c) Francios Gombalt, Christoph Boget, Ville Virta and Vincent Ripoll
# GPL - see COPYING for details

"""Given a list of Abstract Cards in a set, write a XML file compatable with
   the Anarch Revolt Deck Builder's XML inventory format."""

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


class WriteArdbInvXML(ArdbInfo):
    """Reformat cardset to elementTree and export it to a ARDB
       compatible XML Inventory file."""

    def gen_tree(self, dCards):
        """Creates the actual XML document into memory."""
        # pylint: disable-msg=R0914
        # Need this many local variables to create proper XML tree
        oRoot = Element('inventory')

        sDateWritten = time.strftime('%Y-%m-%d', time.localtime())
        oRoot.attrib['generator'] = "Sutekh [ %s ]" % self.sVersionString
        oRoot.attrib['formatVersion'] = self.sFormatVersion
        oRoot.attrib['databaseVersion'] = self.sDatabaseVersion
        oDateElem = SubElement(oRoot, 'date')
        oDateElem.text = sDateWritten

        dVamps, dCryptStats = self._extract_crypt(dCards)
        (dLib, iLibSize) = self._extract_library(dCards)

        oCryptElem = SubElement(oRoot, 'crypt', size=str(dCryptStats['size']))
        self.format_vamps(oCryptElem, dVamps)

        oLibElem = SubElement(oRoot, 'library', size=str(iLibSize))
        self.format_library(oLibElem, dLib)

        pretty_xml(oRoot)
        return oRoot

    # pylint: disable-msg=R0201
    # these are mthods for consistency
    def format_vamps(self, oCryptElem, dVamps):
        """Convert the Vampire dictionary into elementtree representation."""
        dCombinedVamps = {}
        # ARDB inventory doesn't seperate cards by set, although it's included
        # in the XML file, so we need to combine things so there's only 1
        # entry per card
        for tKey, iNum in dVamps.iteritems():
            iNum = dVamps[tKey]
            iId, sName, sSet = tKey
            iId = tKey[0]
            sName = tKey[1]
            dCombinedVamps.setdefault(iId, [sName, sSet, 0])
            dCombinedVamps[iId][2] += iNum
        for iId, (sName, sSet, iNum) in sorted(dCombinedVamps.iteritems(),
                key=lambda x: x[1][0]):
            # pylint: disable-msg=E1101
            # IAbstractCard confuses pylint
            oCard = IAbstractCard(sName)
            oCardElem = SubElement(oCryptElem, 'vampire',
                    databaseID=str(iId), have=str(iNum), spare='0', need='0')
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

    def format_library(self, oLibElem, dLib):
        """Format the dictionary of library cards for the element tree."""
        # pylint: disable-msg=R0914
        # Need this many local variables to create proper XML tree
        dCombinedLib = {}
        for tKey, iNum in dLib.iteritems():
            iNum = dLib[tKey]
            iId = tKey[0]
            sName = tKey[1]
            sSet = tKey[3]
            dCombinedLib.setdefault(iId, [sName, sSet, 0])
            dCombinedLib[iId][2] += iNum
        for iId, (sName, sSet, iNum) in sorted(dCombinedLib.iteritems(),
                key=lambda x: x[1][0]):
            oCardElem = SubElement(oLibElem, 'card', databaseID=str(iId),
                    have=str(iNum), spare='0', need='0')
            oNameElem = SubElement(oCardElem, 'name')
            sName = escape_ardb_name(sName)
            oNameElem.text = sName
            oSetElem = SubElement(oCardElem, 'set')
            oSetElem.text = sSet

    # pylint: enable-msg=R0201

    def write(self, fOut, oCardIter):
        """Takes filename, deck details and a dictionary of cards, of the
           form dCard[(id,name)] = count and writes the file."""
        dCards = self._get_cards(oCardIter)
        oRoot = self.gen_tree(dCards)
        ElementTree(oRoot).write(fOut)

    def gen_xml_string(self, oCardIter):
        """Generate string XML representation"""
        dCards = self._get_cards(oCardIter)
        oRoot = self.gen_tree(dCards)
        return tostring(oRoot)


