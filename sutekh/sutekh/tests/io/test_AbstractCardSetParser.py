# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Abstract Card Set parser"""

import unittest
import os
from io import StringIO

from sutekh.base.core.BaseTables import (PhysicalCardSet,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.core.CardSetHolder import CardSetHolder
from sutekh.base.tests.TestUtils import make_card

from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.XmlFileHandling import AbstractCardSetXmlFile
from sutekh.tests.core.test_PhysicalCardSet import (CARD_SET_NAMES,
                                                    ABSTRACT_CARDS)
from sutekh.tests.TestCore import SutekhTest

ACS_EXAMPLE_1 = ('<abstractcardset author="A test author" '
                 'comment="A test comment" name="Test Set 1" '
                 'sutekh_xml_version="1.1"><annotations /><card count="1" '
                 'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" '
                 '/><card count="1" id="1" name=".44 Magnum" /><card '
                 'count="1" id="2" name="AK-47" /><card count="1" id="14" '
                 'name="Abombwe" /></abstractcardset>')

ACS_EXAMPLE_2 = ('<abstractcardset author="A test author" '
                 'comment="A test comment" name="Test Set 2" '
                 'sutekh_xml_version="1.1"><annotations /><card count="2" '
                 'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" '
                 '/><card count="2" id="2" name=".44 Magnum" /><card '
                 'count="2" id="2" name="AK-47" /><card count="2" id="14" '
                 'name="Abombwe" /></abstractcardset>')


class AbstractCardSetParserTest(SutekhTest):
    """class for the Abstract Card Set Parser"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_abstract_cs_parser(self):
        """Test abstract card set parser"""
        # Support for everything except reading has been removed.
        # It is expected that reading in an ACS will create an
        # equivalent PCS.
        self.maxDiff = None

        oParser = AbstractCardSetParser()

        sTempFileName = self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(ACS_EXAMPLE_1)
        fOut.close()

        oHolder = CardSetHolder()
        oParser.parse(StringIO(ACS_EXAMPLE_2), oHolder)
        oHolder.create_pcs()
        fIn = open(sTempFileName, 'r')
        oHolder = CardSetHolder()
        oParser.parse(fIn, oHolder)
        oHolder.create_pcs()
        fIn.close()

        oCardSet1 = IPhysicalCardSet("(ACS) " + CARD_SET_NAMES[0])
        oCardSet2 = IPhysicalCardSet("(ACS) " + CARD_SET_NAMES[1])

        oPhysCard0 = make_card(ABSTRACT_CARDS[0][0], None)
        oPhysCard2 = make_card(ABSTRACT_CARDS[2][0], None)

        self.assertEqual(len(oCardSet1.cards), 5)
        self.assertEqual(len(oCardSet2.cards), 9)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=oPhysCard0.id).count(), 3)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=oPhysCard2.id).count(), 2)

        PhysicalCardSet.delete(oCardSet1.id)
        oFile = AbstractCardSetXmlFile()
        self.assertRaises(IOError, oFile.read)
        oFile = AbstractCardSetXmlFile(sTempFileName)
        oFile.read()
        oCardSet1 = IPhysicalCardSet("(ACS) Test Set 1")
        self.assertEqual(len(oCardSet1.cards), 5)
        oFile.delete()
        self.assertFalse(os.path.exists(sTempFileName))
        self.assertRaises(RuntimeError, oFile.write, '(ACS) Test Set 1')

        oHolder = CardSetHolder()
        self.assertRaises(IOError, oParser.parse, StringIO(
            '<caarrd>%s</caarrd>' % ACS_EXAMPLE_1), oHolder)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
