# test_ZipFileWrapper.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Zip File Wrapper"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.ProgressDialog import SutekhCountLogHandler
import unittest
import zipfile

class ZipFileWrapperTest(SutekhTest):
    """class for the Zip File tests"""
    aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
    aCardSetNames = ['Test Set 1', 'Test Set 2']

    def test_zip_file(self):
        """Test zip file handling"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        # TODO: Create a test zip file with current data
        sTempFileName =  self._create_tmp_file()
        oZipFile = ZipFileWrapper(sTempFileName)

        # TODO: Check it loads correctly

        # Create a test zipfile with old data
        sACS1 = '<abstractcardset author="A test author" ' \
                'comment="A test comment" name="AC Set 1" ' \
                'sutekh_xml_version="1.1"><annotations /><card count="1" ' \
                'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" ' \
                '/><card count="1" id="1" name=".44 Magnum" /><card ' \
                'count="1" id="2" name="AK-47" /><card count="1" id="14" ' \
                'name="Abombwe" /></abstractcardset>'

        sACS2 = '<abstractcardset author="A test author" ' \
                'comment="A test comment" name="AC Set 2" ' \
                'sutekh_xml_version="1.1"><annotations /><card count="2" ' \
                'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" ' \
                '/><card count="2" id="2" name=".44 Magnum" /><card ' \
                'count="2" id="2" name="AK-47" /><card count="2" id="14" ' \
                'name="Abombwe" /></abstractcardset>'

        sPCS1 = '<physicalcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 1" '\
                'sutekh_xml_version="1.2"><annotations /><card count="1" ' \
                'expansion="None Specified" id="11" name="Abebe" /><card ' \
                'count="1" expansion="None Specified" id="1" ' \
                'name=".44 Magnum" /><card count="1" expansion="None ' \
                'Specified" id="8" name="Abbot" /><card count="1" ' \
                'expansion="None Specified" id="2" name="AK-47" /><card ' \
                'count="1" expansion="None Specified" id="14" ' \
                'name="Abombwe" /></physicalcardset>'

        aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
        oAC = IAbstractCard(aAbstractCards[0])
        oPC = IPhysicalCard((oAC, None))
        sLastWriterVersion = "1.0"

        sPhysicalCards = '<cards sutekh_xml_version="%s"><card count="1" ' \
                   'expansion="None Specified" id="%d" name="%s" /></cards>' \
                   % (sLastWriterVersion, oPC.id, oAC.name)

        sTempFileName =  self._create_tmp_file()
        oZipFile = zipfile.ZipFile(sTempFileName, 'w')
        oZipFile.writestr('PhysicalCardList.xml', sPhysicalCards)
        oZipFile.writestr('acs_set_1.xml', sACS1)
        oZipFile.writestr('acs_set_2.xml', sACS2)
        oZipFile.writestr('pcs_set_2.xml', sPCS1)
        oZipFile.close()

        # Check it loads correctly
        oHandler = SutekhCountLogHandler()
        oZipFile = ZipFileWrapper(sTempFileName)
        oZipFile.do_restore_from_zip(oLogHandler=oHandler)
        self.assertEqual(oHandler.fTot, 4)

        oMyCollection = IPhysicalCardSet("My Collection")
        assert(len(oMyCollection.cards) == 1)

        oPhysCardSet1 = IPhysicalCardSet('Test Set 1')

        self.assertEqual(oPhysCardSet1.parent.id, oMyCollection.id)

        self.assertEqual(len(oPhysCardSet1.cards), 5)

        oACSCardSet1 = IPhysicalCardSet("(ACS) AC Set 1")
        oACSCardSet2 = IPhysicalCardSet("(ACS) AC Set 2")

        self.assertEqual(len(oACSCardSet1.cards), 5)
        self.assertEqual(len(oACSCardSet2.cards), 9)

        self.assertEqual(oACSCardSet1.parent, None)
        self.assertEqual(oACSCardSet2.parent, None)

if __name__ == "__main__":
    unittest.main()
