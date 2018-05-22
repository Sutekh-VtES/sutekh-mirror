# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Read physical cards from an XML file which looks like:

   <physicalcardset sutekh_xml_version='1.4' name='SetName' author='Author'
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

from sutekh.base.io.BaseCardSetIO import BaseCardSetParser
from sutekh.io.BaseSutekhXMLParser import BaseSutekhXMLParser


class PhysicalCardSetParser(BaseCardSetParser, BaseSutekhXMLParser):
    """Impement the parser.

       read the tree into an ElementTree, and walk the tree to find the
       cards.
       """
    aSupportedVersions = ['1.4', '1.3', '1.2', '1.1', '1.0']
    sTypeTag = 'physicalcardset'
    sTypeName = 'Physical Card Set list'
