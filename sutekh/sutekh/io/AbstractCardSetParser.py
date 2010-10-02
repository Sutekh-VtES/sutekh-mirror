# AbstractCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read cards from an XML file which looks like:

   <abstractcardset sutekh_xml_version='1.0' name='AbstractCardSetName'
      author='Author' comment='Comment'>
     <annotations>
     Annotations
     </annotations>
     <card id='3' name='Some Card' count='5' />
     <card id='5' name='Some Other Card' count='2' />
   </abstractcardset>
   into a PhysicalCardSet.
   """

from sutekh.io.IOBase import BaseSutekhXMLParser
from sutekh.core.SutekhObjects import MAX_ID_LENGTH


class AbstractCardSetParser(BaseSutekhXMLParser):
    """Impement the parser.

       read the tree into an ElementTree, and walk the tree to find the
       cards.
       """
    aSupportedVersions = ['1.1', '1.0']
    sTypeTag = 'abstractcardset'
    sTypeName = 'Abstract Card Set list'

    def _convert_tree(self, oHolder):
        """Convert the ElementTree into a CardSetHolder"""
        self._check_tree()
        oRoot = self._oTree.getroot()
        # same reasoning as for database upgrades
        # Ensure name fits into column
        oHolder.name = ('(ACS) %s' % oRoot.attrib['name'])[:MAX_ID_LENGTH]
        oHolder.author = oRoot.attrib['author']
        oHolder.comment = oRoot.attrib['comment']
        oHolder.inuse = False
        for oElem in oRoot:
            if oElem.tag == 'annotations':
                oHolder.annotations = oElem.text
            elif oElem.tag == 'card':
                self._parse_card(oElem, oHolder)  # Will use no expansion path
