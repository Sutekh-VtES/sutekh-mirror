# test_ZipFileWrapper.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Zip File Wrapper"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet, PhysicalCardSet
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.gui.ProgressDialog import SutekhCountLogHandler
from sutekh.core.CardSetUtilities import delete_physical_card_set
import unittest
import zipfile

class ZipFileWrapperTest(SutekhTest):
    """class for the Zip File tests"""

    def test_zip_file(self):
        """Test zip file handling"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        sTempFileName =  self._create_tmp_file()
        oZipFile = ZipFileWrapper(sTempFileName)
        aPhysCards = get_phys_cards()

        oMyCollection = PhysicalCardSet(name='My Collection')

        for oCard in aPhysCards:
            oMyCollection.addPhysicalCard(oCard.id)
            oMyCollection.syncUpdate()

        oPhysCardSet1 = PhysicalCardSet(name=aCardSetNames[0],
                parent=oMyCollection)
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        self.assertNotEqual(oPhysCardSet1.parent, None)
        self.assertEqual(oPhysCardSet1.parent.id, oMyCollection.id)

        for iLoop in range(5):
            oPhysCardSet1.addPhysicalCard(aPhysCards[iLoop].id)
            oPhysCardSet1.syncUpdate()
            if iLoop > 3:
                # Add a duplicate
                oPhysCardSet1.addPhysicalCard(aPhysCards[iLoop].id)
                oPhysCardSet1.syncUpdate()

        oPhysCardSet2 = PhysicalCardSet(name=aCardSetNames[1])
        oPhysCardSet2.comment = 'Test 2 comment'
        oPhysCardSet2.author = 'A different author'

        for iLoop in range(2, 7):
            oPhysCardSet2.addPhysicalCard(aPhysCards[iLoop].id)
            oPhysCardSet2.syncUpdate()

        oHandler = SutekhCountLogHandler()
        oZipFile.do_dump_all_to_zip(oHandler)
        self.assertEqual(oHandler.fTot, 3)

        # Check it loads correctly
        # Destroy some existing data
        aCardSet1 = sorted([x.abstractCard.name for x in oPhysCardSet1.cards])
        aCardSet2 = sorted([x.abstractCard.name for x in oPhysCardSet2.cards])

        delete_physical_card_set(oMyCollection.name)
        delete_physical_card_set(oPhysCardSet1.name)

        self.assertEqual(PhysicalCardSet.select().count(), 1)

        oZipFile.do_restore_from_zip(oLogHandler=oHandler)
        self.assertEqual(oZipFile.get_warnings(), [])
        self.assertEqual(oHandler.fTot, 3)

        self.assertEqual(PhysicalCardSet.select().count(), 3)

        oMyCollection = IPhysicalCardSet('My Collection')
        oPhysCardSet1 = IPhysicalCardSet(aCardSetNames[0])
        oPhysCardSet2 = IPhysicalCardSet(aCardSetNames[1])
        self.assertEqual(oPhysCardSet1.comment, 'A test comment')
        self.assertEqual(oPhysCardSet2.author, 'A different author')
        self.assertNotEqual(oPhysCardSet1.parent, None)
        self.assertEqual(oPhysCardSet1.parent.id, oMyCollection.id)
        self.assertEqual(sorted([x.abstractCard.name for x in
            oPhysCardSet1.cards]), aCardSet1)
        self.assertEqual(oPhysCardSet2.parent, None)
        self.assertEqual(sorted([x.abstractCard.name for x in
            oPhysCardSet2.cards]), aCardSet2)

        self.assertEqual(sorted([x.abstractCard.name for x in
            oMyCollection.cards]), sorted([x.abstractCard.name for x in
                aPhysCards]))
        self.assertEqual(len(oPhysCardSet1.cards), 6)
        self.assertEqual(len(oPhysCardSet2.cards), 5)

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

        oAC = IAbstractCard('.44 magnum')
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
