# test_DatabaseUpgrade.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test database upgrading"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.DatabaseUpgrade import copy_to_new_abstract_card_db, \
                                        create_final_copy
from sutekh.core.CardLookup import SimpleLookup
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCardSet, \
    IAbstractCard, IPhysicalCard, IExpansion, IPhysicalCardSet
from sqlobject import sqlhub, connectionForURI
from logging import FileHandler

class DatabaseUpgradeTests(SutekhTest):
    """Class for the database upgrade tests."""

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

        oPC = IPhysicalCard((IAbstractCard(".44 magnum"), IExpansion("Jyhad")))
        oMyCollection.addPhysicalCard(oPC)

        assert list(PhysicalCardSet.select())

        # Attempt upgrade

        oOrigConn = sqlhub.processConnection

        sDbFile = self._create_tmp_file()
        oNewConn = connectionForURI("sqlite://%s" % sDbFile)
        sqlhub.processConnection = oNewConn

        self._setUpDb()

        assert list(AbstractCard.select())

        oCardLookup = SimpleLookup()
        oLogHandler = FileHandler('/dev/null')

        copy_to_new_abstract_card_db(oOrigConn, oNewConn, oCardLookup,
                oLogHandler)

        assert list(AbstractCard.select())
        assert list(PhysicalCardSet.select())

        sqlhub.processConnection = oOrigConn
        # pylint: disable-msg=W0612
        # we aren't interested in aMsgs here
        bResult, aMsgs = create_final_copy(oNewConn, oLogHandler)

        # Check
        self.failUnless(bResult)

        assert list(AbstractCard.select())
        assert list(PhysicalCardSet.select())

        oMagnum = IAbstractCard('.44 magnum')
        assert oMagnum

        oMyCollection = IPhysicalCardSet("My Collection")
        assert oMyCollection.comment == "test comment"
        assert oMyCollection.author == "test author"
        assert list(oMyCollection.cards)

        oPCS1 = IPhysicalCardSet("PCS1")
        assert oPCS1.parent == oMyCollection
