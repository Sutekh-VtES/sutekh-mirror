# PhysicalCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read physical cards from an XML file which looks like:

   <physicalcardset sutekh_xml_version='1.3' name='SetName' author='Author'
      parent='Parent PCS name'>
     <comment>
     Deck Description
     </comment>
     <annotations>
     Annotations
     </annotations>
     <card name='Some Card' count='5' expansion='Some Expansion' />
     <card name='Some Card' count='2'
         expansion='Some Other Expansion' />
     <card name='Some Other Card' count='2'
         expansion='Some Other Expansion' />
   </physicalcardset>

   into a PhysicalCardSet.
   """

from sutekh.io.IOBase import BaseSutekhXMLParser
from sutekh.core.SutekhObjects import MAX_ID_LENGTH


class PhysicalCardSetParser(BaseSutekhXMLParser):
    """Impement the parser.

       read the tree into an ElementTree, and walk the tree to find the
       cards.
       """
    aSupportedVersions = ['1.3', '1.2', '1.1', '1.0']
    sTypeTag = 'physicalcardset'
    sTypeName = 'Physical Card Set list'

    def _convert_tree(self, oHolder):
        """Convert the ElementTree into a CardSetHolder"""
        self._check_tree()
        oRoot = self._oTree.getroot()
        oHolder.name = oRoot.attrib['name'][:MAX_ID_LENGTH]
        oHolder.inuse = False
        # pylint: disable-msg=W0704
        # exceptions does enough for us
        try:
            oHolder.author = oRoot.attrib['author']
        except KeyError:
            pass
        try:
            oHolder.comment = oRoot.attrib['comment']
        except KeyError:
            # Default value for comment is the right thing here
            pass
        try:
            if oRoot.attrib['inuse'] == 'Yes':
                oHolder.inuse = True
        except KeyError:
            pass
        # pylint: enable-msg=W0704

        if oRoot.attrib.has_key('parent'):
            oHolder.parent = oRoot.attrib['parent']

        for oElem in oRoot:
            if oElem.tag == 'comment':
                if oHolder.comment:
                    # We already encontered a comment, so error out
                    raise IOError("Format error. Multiple"
                            " comment values encountered.")
                oHolder.comment = oElem.text
            if oElem.tag == 'annotations':
                if oHolder.annotations:
                    raise IOError("Format error. Multiple"
                            " annotation values encountered.")
                oHolder.annotations = oElem.text
            elif oElem.tag == 'card':
                self._parse_card(oElem, oHolder)
