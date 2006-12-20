# SutekhUtility.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

from sqlobject import *
from SutekhObjects import *
from DatabaseVersion import DatabaseVersion

def refreshTables(aTables,oConn,**kw):
    aTables.reverse()
    for cCls in aTables:
        cCls.dropTable(ifExists=True,connection=oConn)
    aTables.reverse()
    oVerHandler=DatabaseVersion(oConn)
    if not oVerHandler.setVersion(VersionTable,VersionTable.tableversion,oConn):
        return False
    for cCls in aTables:
        cCls.createTable(connection=oConn)
        if not oVerHandler.setVersion(cCls, cCls.tableversion,oConn):
            return False
    return True


