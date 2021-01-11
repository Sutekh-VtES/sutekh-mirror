# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing Card Set handling"""

from io import StringIO
import unittest

from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import (CARD_SET_NAMES,
                                                    make_set_1,
                                                    make_set_2,
                                                    make_set_3)

# pylint: disable=line-too-long
# Long lines for this test data ease comparison with the actual files produced
EXPECTED_1 = """<physicalcardset author="A test author" name="Test Set 1" sutekh_xml_version="1.4">
  <comment>A test comment</comment>
  <annotations />
  <card count="1" expansion="Jyhad" name=".44 Magnum" printing="No Printing" />
  <card count="3" expansion="None Specified" name=".44 Magnum" printing="No Printing" />
  <card count="1" expansion="Lords of the Night" name="AK-47" printing="No Printing" />
  <card count="1" expansion="None Specified" name="AK-47" printing="No Printing" />
  <card count="1" expansion="Keepers of Tradition" name="Aaron's Feeding Razor" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abbot" printing="No Printing" />
  <card count="1" expansion="Third Edition" name="Abbot" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abebe" printing="No Printing" />
  <card count="1" expansion="Legacy of Blood" name="Abombwe" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abombwe" printing="No Printing" />
  <card count="3" expansion="Camarilla Edition" name="Aire of Elation" printing="No Printing" />
  <card count="1" expansion="Promo-20051001" name="Alan Sovereign (Advanced)" printing="No Printing" />
  <card count="1" expansion="Twilight Rebellion" name="An Anarch Manifesto" printing="No Printing" />
  <card count="1" expansion="Third Edition" name="Hektor" printing="Sketch" />
  <card count="1" expansion="Heirs to the Blood" name="Hide the Heart" printing="No Printing" />
  <card count="1" expansion="Jyhad" name="Immortal Grapple" printing="No Printing" />
  <card count="1" expansion="Jyhad" name="Immortal Grapple" printing="Variant Printing" />
  <card count="1" expansion="Keepers of Tradition" name="Immortal Grapple" printing="No Draft Text" />
  <card count="1" expansion="Keepers of Tradition" name="Immortal Grapple" printing="No Printing" />
  <card count="1" expansion="Nights of Reckoning" name="Inez &quot;Nurse216&quot; Villagrande" printing="No Printing" />
  <card count="1" expansion="Dark Sovereigns" name="Scapelli, The Family &quot;Mechanic&quot;" printing="No Printing" />
  <card count="1" expansion="Third Edition" name="Swallowed by the Night" printing="No Draft Text" />
  <card count="1" expansion="Third Edition" name="Swallowed by the Night" printing="No Printing" />
  <card count="1" expansion="Lords of the Night" name="The Path of Blood" printing="No Printing" />
  <card count="2" expansion="Bloodlines" name="The Siamese" printing="No Printing" />
  <card count="1" expansion="Keepers of Tradition" name="Walk of Flame" printing="No Printing" />
  <card count="2" expansion="Third Edition" name="Walk of Flame" printing="No Draft Text" />
  <card count="1" expansion="Third Edition" name="Walk of Flame" printing="No Printing" />
</physicalcardset>"""

EXPECTED_2 = """<physicalcardset author="A test author" name="Test Set 2" sutekh_xml_version="1.4">
  <comment>A formatted test comment
A second line
A third line</comment>
  <annotations>Some Annotations</annotations>
  <card count="1" expansion="Jyhad" name=".44 Magnum" printing="No Printing" />
  <card count="1" expansion="Lords of the Night" name="AK-47" printing="No Printing" />
  <card count="1" expansion="Camarilla Edition" name="Abandoning the Flesh" printing="No Printing" />
  <card count="1" expansion="Third Edition" name="Abbot" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abebe" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abombwe" printing="No Printing" />
  <card count="2" expansion="Dark Sovereigns" name="Alexandra" printing="No Printing" />
</physicalcardset>"""

EXPECTED_3 = """<physicalcardset author="" name="Test Set 2" sutekh_xml_version="1.4">
  <comment>A formatted test comment
A second line
A third line</comment>
  <annotations>Some Annotations</annotations>
  <card count="1" expansion="Jyhad" name=".44 Magnum" printing="No Printing" />
  <card count="1" expansion="Lords of the Night" name="AK-47" printing="No Printing" />
  <card count="1" expansion="Camarilla Edition" name="Abandoning the Flesh" printing="No Printing" />
  <card count="1" expansion="Third Edition" name="Abbot" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abebe" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abombwe" printing="No Printing" />
  <card count="2" expansion="Dark Sovereigns" name="Alexandra" printing="No Printing" />
</physicalcardset>"""

EXPECTED_4 = """<physicalcardset author="A test author" name="Test Set 3" sutekh_xml_version="1.4">
  <comment>A formatted test comment
A second line
A third line</comment>
  <annotations>Some Annotations</annotations>
  <card count="1" expansion="Jyhad" name=".44 Magnum" printing="No Printing" />
  <card count="1" expansion="Lords of the Night" name="AK-47" printing="No Printing" />
  <card count="1" expansion="Camarilla Edition" name="Abandoning the Flesh" printing="No Printing" />
  <card count="1" expansion="Third Edition" name="Abbot" printing="No Printing" />
  <card count="1" expansion="None Specified" name="Abombwe" printing="No Printing" />
  <card count="2" expansion="Dark Sovereigns" name="Alexandra" printing="No Printing" />
  <card count="1" expansion="Anarchs" name="&#201;tienne Fauberge" printing="No Printing" />
</physicalcardset>"""

# pylint: enable=line-too-long


class PhysicalCardSetWriterTests(SutekhTest):
    """class for the Physical Card Set writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_physical_card_set_writer(self):
        """Test physical card set writing"""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = PhysicalCardSetWriter()
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet1))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self._compare_xml_strings(sWriterXML, EXPECTED_1)

        oPCS = IPhysicalCardSet(CARD_SET_NAMES[0])
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPCS))
        self._compare_xml_strings(sData, sWriterXML)
        self._compare_xml_strings(sData, EXPECTED_1)

        oPhysCardSet2 = make_set_2()

        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet2))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self._compare_xml_strings(sWriterXML, EXPECTED_2)

        sTempFileName = self._create_tmp_file()
        oFileXML = PhysicalCardSetXmlFile(sTempFileName)
        oFileXML.write(CARD_SET_NAMES[1])
        fIn = open(sTempFileName, 'r')
        sData = fIn.read()
        self._compare_xml_strings(sData, EXPECTED_2)

        # Unset the author
        oPhysCardSet2.author = None
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet2))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self._compare_xml_strings(sWriterXML, EXPECTED_3)

        # Test with more unicode stuff
        oWriter = PhysicalCardSetWriter()

        oPhysCardSet3 = make_set_3()
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet3))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self._compare_xml_strings(sWriterXML, EXPECTED_4)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
