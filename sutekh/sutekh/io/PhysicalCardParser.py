# PhysicalCardParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read physical cards from an XML file which looks like:

   <cards sutekh_xml_version="1.0">
     <card id='3' name='Some Card' count='5' expansion="Some Expansion" />
     <card id='3' name='Some Card' count='2'
        Expansion="Some Other Expansion" />
     <card id='5' name='Some Other Card' count='2'
       expansion="Some Expansion" />
   </cards>
   into the default PhysicalCardSet 'My Collection'.
   """

from sutekh.io.IOBase import BaseSutekhXMLParser


class PhysicalCardParser(BaseSutekhXMLParser):
    """Implement the PhysicalCard Parser.

       We read the xml file into a ElementTree, then walk the tree to
       extract the cards.
       """
    aSupportedVersions = ['1.0', '0.0']
    sTypeTag = 'cards'
    sTypeName = 'Physical card list'

    # pylint: disable-msg=R0201

    def _convert_tree(self, oHolder):
        """parse the elementtree into a card set holder"""
        self._check_tree()
        oHolder.name = "My Collection"
        oRoot = self._oTree.getroot()
        for oElem in oRoot:
            if oElem.tag == 'card':
                self._parse_card(oElem, oHolder)
