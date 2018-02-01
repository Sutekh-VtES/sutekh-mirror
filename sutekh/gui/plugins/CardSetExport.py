# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008, 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to standard writers"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseExport import BaseCardSetExport
from sutekh.io.WriteJOL import WriteJOL
from sutekh.io.WriteLackeyCCG import WriteLackeyCCG
from sutekh.io.WriteArdbXML import WriteArdbXML
from sutekh.io.WriteArdbInvXML import WriteArdbInvXML
from sutekh.io.WriteELDBInventory import WriteELDBInventory
from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.io.WriteTWDAText import WriteTWDAText
from sutekh.io.WriteVEKNForum import WriteVEKNForum


class CardSetExport(SutekhPlugin, BaseCardSetExport):
    """Provides a dialog for selecting a filename, then calls on
       the appropriate writer to produce the required output."""

    EXPORTERS = {
        'JOL': (WriteJOL, 'Export to JOL format', 'jol.txt'),
        'Lackey': (WriteLackeyCCG, 'Export to Lackey CCG format',
                   'lackey.txt'),
        'ARDB Text': (WriteArdbText, 'Export to ARDB Text', 'ardb.txt'),
        'TWDA Text': (WriteTWDAText, 'Export to text formated used in the'
                      ' TWDA', 'twda.txt'),
        'vekn.net': (WriteVEKNForum,
                     'BBcode output for the V:EKN Forums', 'vekn.txt'),
        'FELDB Inv': (WriteELDBInventory,
                      'Export to ELDB CSV Inventory File', 'eldb.csv',
                      'CSV Files', ['*.csv']),
        'FELDB Deck': (WriteELDBDeckFile, 'Export to ELDB ELD Deck File',
                       'eldb.eld', 'ELD Files', ['*.eld']),
        'ARDB Inv': (WriteArdbInvXML, 'Export to ARDB Inventory XML File',
                     'inv.ardb.xml', 'XML Files', ['*.xml']),
        'ARDB Deck': (WriteArdbXML, 'Export to ARDB Deck XML File',
                      'ardb.xml', 'XML Files', ['*.xml']),
    }


plugin = CardSetExport
