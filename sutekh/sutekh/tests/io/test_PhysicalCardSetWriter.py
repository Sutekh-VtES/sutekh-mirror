# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing Card Set handling"""

from StringIO import StringIO
import unittest

from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import (CARD_SET_NAMES,
                                                    make_set_1,
                                                    make_set_2)

# pylint: disable=line-too-long
# Long lines for this test data ease comparison with the actual files produced
EXPECTED_1 = """<physicalcardset author="A test author" name="Test Set 1" sutekh_xml_version="1.3">
  <comment>A test comment</comment>
  <annotations />
  <card count="1" expansion="Jyhad" name=".44 Magnum" />
  <card count="3" expansion="None Specified" name=".44 Magnum" />
  <card count="1" expansion="Lords of the Night" name="AK-47" />
  <card count="1" expansion="None Specified" name="AK-47" />
  <card count="1" expansion="Keepers of Tradition" name="Aaron's Feeding Razor" />
  <card count="1" expansion="None Specified" name="Abbot" />
  <card count="1" expansion="Third Edition" name="Abbot" />
  <card count="1" expansion="None Specified" name="Abebe" />
  <card count="1" expansion="Legacy of Blood" name="Abombwe" />
  <card count="1" expansion="None Specified" name="Abombwe" />
  <card count="3" expansion="Camarilla Edition" name="Aire of Elation" />
  <card count="1" expansion="Promo-20051001" name="Alan Sovereign (Advanced)" />
  <card count="1" expansion="Twilight Rebellion" name="An Anarch Manifesto" />
  <card count="1" expansion="Heirs to the Blood" name="Hide the Heart" />
  <card count="2" expansion="Jyhad" name="Immortal Grapple" />
  <card count="2" expansion="Keepers of Tradition" name="Immortal Grapple" />
  <card count="1" expansion="Nights of Reckoning" name="Inez &quot;Nurse216&quot; Villagrande" />
  <card count="1" expansion="Dark Sovereigns" name="Scapelli, The Family &quot;Mechanic&quot;" />
  <card count="2" expansion="Third Edition" name="Swallowed by the Night" />
  <card count="1" expansion="Lords of the Night" name="The Path of Blood" />
  <card count="2" expansion="Bloodlines" name="The Siamese" />
  <card count="1" expansion="Keepers of Tradition" name="Walk of Flame" />
  <card count="2" expansion="Third Edition" name="Walk of Flame" />
</physicalcardset>"""

EXPECTED_2 = """<physicalcardset author="A test author" name="Test Set 2" sutekh_xml_version="1.3">
  <comment>A formatted test comment
A second line
A third line</comment>
  <annotations>Some Annotations</annotations>
  <card count="1" expansion="Jyhad" name=".44 Magnum" />
  <card count="1" expansion="Lords of the Night" name="AK-47" />
  <card count="1" expansion="Camarilla Edition" name="Abandoning the Flesh" />
  <card count="1" expansion="Third Edition" name="Abbot" />
  <card count="1" expansion="None Specified" name="Abebe" />
  <card count="1" expansion="None Specified" name="Abombwe" />
  <card count="2" expansion="Dark Sovereigns" name="Alexandra" />
</physicalcardset>"""

EXPECTED_3 = """<physicalcardset author="" name="Test Set 2" sutekh_xml_version="1.3">
  <comment>A formatted test comment
A second line
A third line</comment>
  <annotations>Some Annotations</annotations>
  <card count="1" expansion="Jyhad" name=".44 Magnum" />
  <card count="1" expansion="Lords of the Night" name="AK-47" />
  <card count="1" expansion="Camarilla Edition" name="Abandoning the Flesh" />
  <card count="1" expansion="Third Edition" name="Abbot" />
  <card count="1" expansion="None Specified" name="Abebe" />
  <card count="1" expansion="None Specified" name="Abombwe" />
  <card count="2" expansion="Dark Sovereigns" name="Alexandra" />
</physicalcardset>"""

# pylint: enable=line-too-long


class PhysicalCardSetWriterTests(SutekhTest):
    """class for the Physical Card Set writer tests"""
    # pylint: disable=R0904
    # R0904 - unittest.TestCase, so many public methods

    def test_physical_card_set_writer(self):
        """Test physical card set writing"""
        # pylint: disable=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = PhysicalCardSetWriter()
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet1))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self.assertEqual(len(sWriterXML), len(EXPECTED_1))
        self.assertEqual(sWriterXML, EXPECTED_1)

        oPCS = IPhysicalCardSet(CARD_SET_NAMES[0])
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPCS))
        self.assertEqual(len(sData), len(EXPECTED_1))
        self.assertEqual(sData, sWriterXML)
        self.assertEqual(sData, EXPECTED_1)

        oPhysCardSet2 = make_set_2()

        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet2))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self.assertEqual(len(sWriterXML), len(EXPECTED_2))
        self.assertEqual(sWriterXML, EXPECTED_2)

        sTempFileName = self._create_tmp_file()
        oFileXML = PhysicalCardSetXmlFile(sTempFileName)
        oFileXML.write(CARD_SET_NAMES[1])
        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        self.assertEqual(len(sData), len(EXPECTED_2))
        self.assertEqual(sData, EXPECTED_2)

        # Unset the author
        oPhysCardSet2.author = None
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet2))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self.assertEqual(len(sWriterXML), len(EXPECTED_3))
        self.assertEqual(sWriterXML, EXPECTED_3)


if __name__ == "__main__":
    unittest.main()
