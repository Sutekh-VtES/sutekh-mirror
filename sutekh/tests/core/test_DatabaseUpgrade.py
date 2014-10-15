# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test database upgrading"""

import sys
from sutekh.tests.TestCore import SutekhTest
from sutekh.base.tests.TestUtils import make_null_handler
from sutekh.tests import create_db
from sutekh.core.DatabaseUpgrade import DBUpgradeManager
from sutekh.base.core.BaseDBManagement import copy_to_new_abstract_card_db
from sutekh.base.core.CardLookup import SimpleLookup
from sutekh.base.core.BaseObjects import (AbstractCard, PhysicalCardSet,
                                          AbstractCardAdapter,
                                          PhysicalCardAdapter,
                                          ExpansionAdapter, IPhysicalCardSet)
from sqlobject import sqlhub, connectionForURI


class DatabaseUpgradeTests(SutekhTest):
    """Class for the database upgrade tests."""
    # pylint: disable-msg=R0904
    # R0904 - unittest.TestCase, so many public methods

    def test_copy_to_new_ac_db(self):
        """Test copying an existing database to a freshly created one using
           copy_to_new_abstract_card_db."""
        # Create some database content

        oMyCollection = PhysicalCardSet(name="My Collection")
        oMyCollection.comment = "test comment"
        oMyCollection.author = "test author"

        oPCS1 = PhysicalCardSet(name="PCS1", parent=oMyCollection)
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint

        oPC = PhysicalCardAdapter((AbstractCardAdapter(".44 magnum"),
            ExpansionAdapter("Jyhad")))
        oMyCollection.addPhysicalCard(oPC)

        assert list(PhysicalCardSet.select())

        iPCSCount = PhysicalCardSet.select().count()
        iACCount = AbstractCard.select().count()

        # Attempt upgrade

        oOrigConn = sqlhub.processConnection

        sDbFile = self._create_tmp_file()
        # windows is different, since we don't have a starting / for the path
        if sys.platform.startswith("win"):
            oNewConn = connectionForURI("sqlite:///%s" % sDbFile)
        else:
            oNewConn = connectionForURI("sqlite://%s" % sDbFile)
        sqlhub.processConnection = oNewConn

        create_db()

        assert list(AbstractCard.select())

        oCardLookup = SimpleLookup()
        oLogHandler = make_null_handler()

        copy_to_new_abstract_card_db(oOrigConn, oNewConn, oCardLookup,
                oLogHandler)

        assert list(AbstractCard.select())
        assert list(PhysicalCardSet.select())

        self.assertEqual(AbstractCard.select().count(), iACCount)
        self.assertEqual(PhysicalCardSet.select().count(), iPCSCount)

        sqlhub.processConnection = oOrigConn
        oDBUpgrade = DBUpgradeManager()
        bResult, _aMsgs = oDBUpgrade.create_final_copy(oNewConn, oLogHandler)

        # Check
        self.failUnless(bResult)

        assert list(AbstractCard.select())
        assert list(PhysicalCardSet.select())

        self.assertEqual(AbstractCard.select().count(), iACCount)
        self.assertEqual(PhysicalCardSet.select().count(), iPCSCount)

        oMagnum = AbstractCardAdapter('.44 magnum')
        assert oMagnum

        oMyCollection = IPhysicalCardSet("My Collection")
        assert oMyCollection.comment == "test comment"
        assert oMyCollection.author == "test author"
        assert list(oMyCollection.cards)

        oPCS1 = IPhysicalCardSet("PCS1")
        assert oPCS1.parent == oMyCollection
        oNewConn.close()
