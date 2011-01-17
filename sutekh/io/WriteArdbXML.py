# WriteArdbXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based off the Anarach Revolt Deck Builder xml support,
# ARDB (c) Francios Gombalt, Christoph Boget, Ville Virta and Vincent Ripoll
# GPL - see COPYING for details

"""Given a list of Abstract Cards in a set, write a XML file compatable with
   the Anarch Revolt Deck Builder."""

from sutekh.core.SutekhObjects import canonical_to_csv
from sutekh.core.ArdbInfo import ArdbInfo
from sutekh.io.IOBase import BaseXMLWriter
import time
# pylint: disable-msg=E0611, F0401
# xml.etree is a python2.5 thing
try:
    from xml.etree.ElementTree import Element, SubElement
except ImportError:
    from elementtree.ElementTree import Element, SubElement
# pylint: enable-msg=E0611, F0401


class WriteArdbXML(ArdbInfo, BaseXMLWriter):
    """Reformat cardset to elementTree and export it to a ARDB
       compatible XML file."""

    def _add_date_version(self, oRoot):
        """Add the standard data to the root element"""
        sDateWritten = time.strftime('%Y-%m-%d', time.localtime())
        oRoot.attrib['generator'] = "Sutekh [ %s ]" % self.sVersionString
        oRoot.attrib['formatVersion'] = self.sFormatVersion
        oRoot.attrib['databaseVersion'] = self.sDatabaseVersion
        oDateElem = SubElement(oRoot, 'date')
        oDateElem.text = sDateWritten

    # pylint: disable-msg=R0201
    # Methods so they're available to the subclasses
    def _ardb_crypt_card(self, oCardElem, oAbsCard, sSet):
        """Fill in name, set and advanced elements for a crypt card"""
        oAdvElem = SubElement(oCardElem, 'adv')
        oNameElem = SubElement(oCardElem, 'name')
        sName = canonical_to_csv(oAbsCard.name)
        if oAbsCard.level is not None:
            oAdvElem.text = 'Advanced'
            # This is a bit hackish
            oNameElem.text = sName.replace(' (Advanced)', '')
        else:
            oNameElem.text = sName
        oSetElem = SubElement(oCardElem, 'set')
        oSetElem.text = sSet

    def _ardb_lib_card(self, oCardElem, oAbsCard, sSet):
        """Fill in name and set for a library card"""
        oNameElem = SubElement(oCardElem, 'name')
        oNameElem.text = canonical_to_csv(oAbsCard.name)
        oSetElem = SubElement(oCardElem, 'set')
        oSetElem.text = sSet

    # pylint: enable-msg=R0201

    def _gen_tree(self, oHolder):
        """Creates the actual XML document into memory."""
        dCards = self._get_cards(oHolder.cards)
        dVamps, dCryptStats = self._extract_crypt(dCards)
        dLib, iLibSize = self._extract_library(dCards)
        oRoot = Element('deck')

        self._add_date_version(oRoot)

        oNameElem = SubElement(oRoot, 'name')
        oNameElem.text = oHolder.name
        oAuthElem = SubElement(oRoot, 'author')
        oAuthElem.text = oHolder.author
        oDescElem = SubElement(oRoot, 'description')
        oDescElem.text = oHolder.comment

        oCryptElem = SubElement(oRoot, 'crypt', size=str(dCryptStats['size']),
                min=str(dCryptStats['min']), max=str(dCryptStats['max']),
                avg='%.2f' % dCryptStats['avg'])
        self.format_vamps(oCryptElem, dVamps)
        oLibElem = SubElement(oRoot, 'library', size=str(iLibSize))
        self.format_library(oLibElem, dLib)
        return oRoot

    def format_vamps(self, oCryptElem, dVamps):
        """Convert the Vampire dictionary into ElementTree representation."""
        for (oCard, sSet), iNum in sorted(dVamps.iteritems(),
                key=lambda x: (x[0][0].name, x[0][1], x[1])):
            # This won't match the ARDB ID's, unless by chance.
            # It looks like that should not be an issue as ARDB will
            # use the name if the IDs don't match
            oCardElem = SubElement(oCryptElem, 'vampire',
                    databaseID=str(oCard.id), count=str(iNum))
            self._ardb_crypt_card(oCardElem, oCard, sSet)
            oDiscElem = SubElement(oCardElem, 'disciplines')
            oDiscElem.text = self._gen_disciplines(oCard)
            oClanElem = SubElement(oCardElem, 'clan')
            oCapElem = SubElement(oCardElem, 'capacity')
            if len(oCard.creed) > 0:
                # ARDB seems to treat all Imbued as being of the same clan
                # Should we do an Imbued:Creed thing?
                oClanElem.text = 'Imbued'
                oCapElem.text = str(oCard.life)
            else:
                oClanElem.text = [x.name for x in oCard.clan][0]
                oCapElem.text = str(oCard.capacity)
            oGrpElem = SubElement(oCardElem, 'group')
            oGrpElem.text = str(oCard.group)
            # ARDB doesn't handle sect specifically
            # No idea how ARDB represents independant titles -
            # this seems set when the ARDB database is created, and is
            # not in the ARDB codebase
            if len(oCard.title) > 0:
                oTitleElem = SubElement(oCardElem, 'title')
                oTitleElem.text = [oC.name for oC in oCard.title][0]
            oTextElem = SubElement(oCardElem, 'text')
            oTextElem.text = oCard.text

    def format_library(self, oLibElem, dLib):
        """Format the dictionary of library cards for the element tree."""
        for (oCard, sTypeString, sSet), iNum in sorted(dLib.iteritems(),
                key=lambda x: (x[0][0].name, x[0][1], x[1])):
            oCardElem = SubElement(oLibElem, 'card', databaseID=str(oCard.id),
                    count=str(iNum))
            self._ardb_lib_card(oCardElem, oCard, sSet)
            if oCard.costtype is not None:
                oCostElem = SubElement(oCardElem, 'cost')
                oCostElem.text = "%d %s" % (oCard.cost, oCard.costtype)
            if len(oCard.clan) > 0:
                # ARDB also strores things like "requires a prince"
                # we don't, so too bad
                oReqElem = SubElement(oCardElem, 'requirement')
                oReqElem.text = ".".join([x.name for x in oCard.clan])
            oTypeElem = SubElement(oCardElem, 'type')
            oTypeElem.text = sTypeString
            # Not sure if this does quite the right thing here
            if len(oCard.discipline) > 0:
                oDiscElem = SubElement(oCardElem, 'disciplines')
                oDiscElem.text = self._gen_disciplines(oCard)
            oTextElem = SubElement(oCardElem, 'text')
            oTextElem.text = oCard.text
