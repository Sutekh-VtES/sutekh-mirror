# WriteArdbInvXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Based off the Anarach Revolt Deck Builder xml support,
# ARDB (c) Francios Gombalt, Christoph Boget, Ville Virta and Vincent Ripoll
# GPL - see COPYING for details

"""Given a list of Abstract Cards in a set, write a XML file compatable with
   the Anarch Revolt Deck Builder's XML inventory format."""

from sutekh.io.WriteArdbXML import WriteArdbXML
# pylint: disable-msg=E0611, F0401
# xml.etree is a python2.5 thing
try:
    from xml.etree.ElementTree import Element, SubElement
except ImportError:
    from elementtree.ElementTree import Element, SubElement
# pylint: enable-msg=E0611, F0401


class WriteArdbInvXML(WriteArdbXML):
    """Reformat cardset to elementTree and export it to a ARDB
       compatible XML Inventory file."""

    def _gen_tree(self, oHolder):
        """Creates the actual XML document into memory."""
        dCards = self._get_cards(oHolder.cards)
        dVamps, dCryptStats = self._extract_crypt(dCards)
        dLib, iLibSize = self._extract_library(dCards)

        oRoot = Element('inventory')
        self._add_date_version(oRoot)

        oCryptElem = SubElement(oRoot, 'crypt', size=str(dCryptStats['size']))
        dCombinedVamps = self._group_sets(dVamps)
        self.format_vamps(oCryptElem, dCombinedVamps)
        oLibElem = SubElement(oRoot, 'library', size=str(iLibSize))
        dCombinedLib = self._group_sets(dLib)
        self.format_library(oLibElem, dCombinedLib)
        return oRoot

    def format_vamps(self, oCryptElem, dCombinedVamps):
        """Convert the Vampire dictionary into ElementTree representation."""
        for oCard, (iNum, sSet) in sorted(dCombinedVamps.iteritems(),
                key=lambda x: (x[0].name, x[1][1], x[1][0])):
            # This won't match the ARDB ID's, unless by chance.
            # It looks like that should not be an issue as ARDB will
            # use the name if the IDs don't match
            oCardElem = SubElement(oCryptElem, 'vampire',
                    databaseID=str(oCard.id), have=str(iNum),
                    spare='0', need='0')
            self._ardb_crypt_card(oCardElem, oCard, sSet)

    def format_library(self, oLibElem, dCombinedLib):
        """Format the dictionary of library cards for the element tree."""
        for oCard, (iNum, _sType, sSet) in sorted(dCombinedLib.iteritems(),
                key=lambda x: (x[0].name, x[1][2], x[1][0])):
            oCardElem = SubElement(oLibElem, 'card', databaseID=str(oCard.id),
                    have=str(iNum), spare='0', need='0')
            self._ardb_lib_card(oCardElem, oCard, sSet)
