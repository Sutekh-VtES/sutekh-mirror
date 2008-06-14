# test_IdentifyXMLFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test IdentifyXMLFile handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard
import unittest

class TestIdentifyXMLFile(SutekhTest):
    """class for the IdentifyXMLFile tests"""

    def test_identify_xml_file(self):
        """Test IdentifyXMLFile"""
        # pylint: disable-msg=E1101
        # E1101: SQLObject + PyProtocols magic confuses pylint
        aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
        # test IO

        oAC = IAbstractCard(aAbstractCards[0])
        oPC = IPhysicalCard((oAC, None))
        sLastWriterVersion = "1.0"

        sExample = '<cards sutekh_xml_version="%s"><card count="1" ' \
                   'expansion="None Specified" id="%d" name="%s" /></cards>' \
                   % (sLastWriterVersion, oPC.id, oAC.name)

        sExampleACS = '<abstractcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 1" ' \
                'sutekh_xml_version="1.1"><annotations /><card count="1" ' \
                'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" ' \
                '/><card count="1" id="1" name=".44 Magnum" /><card ' \
                'count="1" id="2" name="AK-47" /><card count="1" id="14" ' \
                'name="Abombwe" /></abstractcardset>'

        sExamplePCS = '<physicalcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 1" '\
                'sutekh_xml_version="1.2"><annotations /><card count="1" ' \
                'expansion="None Specified" id="11" name="Abebe" />' \
                '</physicalcardset>'

        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(sExample)
        fOut.close()

        oIdFile = IdentifyXMLFile()
        oIdFile.id_file(sTempFileName)
        self.assertEqual(oIdFile.type, 'PhysicalCard')

        oIdFile.parse_string(sExample)
        self.assertEqual(oIdFile.type, 'PhysicalCard')

        oIdFile.parse_string('garbage input')
        self.assertEqual(oIdFile.type, 'Unknown')

        oIdFile.parse_string(sExampleACS)
        self.assertEqual(oIdFile.type, 'AbstractCardSet')

        oIdFile.parse_string(sExamplePCS)
        self.assertEqual(oIdFile.type, 'PhysicalCardSet')

if __name__ == "__main__":
    unittest.main()
