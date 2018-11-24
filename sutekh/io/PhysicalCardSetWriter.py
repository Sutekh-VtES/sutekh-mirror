# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Write physical cards from a PhysicalCardSet

   Save to an XML file which looks like:
   <physicalcardset sutekh_xml_version='1.4' name='SetName' author='Author'>
     <comment>Deck Description</comment>
     <annotations> Various annotations
     More annotations
     </annotations>
     <card name='Some Card' count='5' expansion='Some Expansion' />
     <card name='Some Card' count='2'
        expansion='Some Other Expansion' />
     <card name='Some Other Card' count='2'
        expansion='Some Other Expansion' printing="Some Printing" />
   </physicalcardset>
   """

from sutekh.base.io.BaseCardSetIO import BaseCardXMLWriter


class PhysicalCardSetWriter(BaseCardXMLWriter):
    """Writer for Physical Card Sets.

       We generate an ElementTree representation of the Card Set, which
       can then easily be converted to an appropriate XML representation.
       """
    sMyVersion = "1.4"
    sTypeTag = "physicalcardset"
    sVersionTag = "sutekh_xml_version"
