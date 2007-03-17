# SutekhCli.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Minor modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.SutekhObjects import *
from sutekh.SutekhUtility import *
from sutekh.DatabaseUpgrade import *
from sutekh.PhysicalCardParser import PhysicalCardParser
from sutekh.PhysicalCardWriter import PhysicalCardWriter
from sutekh.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.AbstractCardSetParser import AbstractCardSetParser
from sutekh.AbstractCardSetWriter import AbstractCardSetWriter
from sutekh.DatabaseVersion import DatabaseVersion
from sutekh.IdentifyXMLFile import IdentifyXMLFile
from sqlobject import *
import zipfile 
import sys, optparse, os, tempfile

def parseOptions(aArgs):
    oP = optparse.OptionParser(usage="usage: %prog [options]",version="%prog 0.1")
    oP.add_option("-d","--db",
                  type="string",dest="db",default=None,
                  help="Database URI. [./sutekh.db]")
    oP.add_option("-r","--ww-file",
                  type="string",dest="ww_file",default=None,
                  help="HTML file (probably from WW website) to read cards from.")
    oP.add_option("--ruling-file",
                  type="string",dest="ruling_file",default=None,
                  help="HTML file (probably from WW website) to read rulings from.")
    oP.add_option("-c","--refresh-tables",
                  action="store_true",dest="refresh_tables",default=False,
                  help="Drop (if possible) and recreate database tables.")
    oP.add_option("--refresh-ruling-tables",
                  action="store_true",dest="refresh_ruling_tables",default=False,
                  help="Drop (if possible) and recreate rulings tables only.")
    oP.add_option("--refresh-physical-card-tables",
                  action="store_true",dest="refresh_physical_card_tables",default=False,
                  help="Drop (if possible) and recreate physical card tables only.")
    oP.add_option("--sql-debug",
                  action="store_true",dest="sql_debug",default=False,
                  help="Print out SQL statements.")
    oP.add_option("-s","--save-physical-cards-to",
                  type="string",dest="save_physical_cards_to",default=None,
                  help="Write an XML description of the list of physical cards to the given file.")
    oP.add_option("-l","--read-physical-cards-from",
                  type="string",dest="read_physical_cards_from",default=None,
                  help="Read physical card list from the given XML file.")
    oP.add_option("--save-pcs",
                  type="string",dest="save_pcs",default=None,
                  help="Save the given Physical Card Set to an XML file (by default named <pcsname>.xml).")
    oP.add_option("--pcs-filename",
                  type="string",dest="pcs_filename",default=None,
                  help="Give an alternative filename to save the Physical Card Set as")
    oP.add_option("--save-all-pcs",
                  action="store_true",dest="save_all_pcss",default=False,
                  help="Save all Physical Card Sets in the database to files - Cannot be used with --save-pcs.")
    oP.add_option("--read-pcs",
                  type="string",dest="read_pcs",default=None,
                  help="Load a Physical Card Set from the given XML file.")
    oP.add_option("--save-acs",
                  type="string",dest="save_acs",default=None,
                  help="Save the given Abstract Card Set to an XML file (by default named <acsname>.xml).")
    oP.add_option("--acs-filename",
                  type="string",dest="acs_filename",default=None,
                  help="Give an alternative filename to save the Abstract Card Set as")
    oP.add_option("--save-all-acs",
                  action="store_true",dest="save_all_acss",default=False,
                  help="Save all Abstract Card Sets in the database to files - Cannot be used with --save-acs.")
    oP.add_option("--read-acs",
                  type="string",dest="read_acs",default=None,
                  help="Load an Abstract Card Set from the given XML file.")
    oP.add_option("--reload",action="store_true",dest="reload",default=False,
                  help="Dump the physical card list and all card sets and reload them - \
intended to be used with -c and refreshing the abstract card list")
    oP.add_option("--upgrade-db",\
                  action="store_true",dest="upgrade_db",default=False,\
                  help="Attempt to upgrade a database to the latest version. Cannot be used with --refresh-tables")
    oP.add_option("--dump-zip",\
            type="string",dest="dump_zip_name",default=None,\
            help="Dump the PhysicalCard list and all the CardSets to the given zipfile")
    oP.add_option("--restore-zip",\
            type="string",dest="restore_zip_name",default=None,\
            help="Restore everything from the given zipfile")

    return oP, oP.parse_args(aArgs)

def readPhysicalCards(sXmlFile):
    oP = PhysicalCardParser()
    oP.parse(file(sXmlFile,'rU'))

def writePhysicalCards(sXmlFile):
    oW = PhysicalCardWriter()
    fOut = file(sXmlFile,'w')
    oW.write(fOut)
    fOut.close()

def readPhysicalCardSet(sXmlFile):
    oP = PhysicalCardSetParser()
    oP.parse(file(sXmlFile,'rU'))

def writePhysicalCardSet(sPhysicalCardSetName,sXmlFile):
    oW = PhysicalCardSetWriter()
    if sXmlFile is None:
        filename=sPhysicalCardSetName.replace(" ","_") # I hate spaces in filenames
        fOut=file(filename,'w')
    else:
        fOut=file(sXmlFile,'w')
    oW.write(fOut,sPhysicalCardSetName)
    fOut.close()

def writeAllPhysicalCardSets(dir=''):
    oPhysicalCardSets = PhysicalCardSet.select()
    aList=[];
    for pcs in oPhysicalCardSets:
        sFName=pcs.name
        sFName=sFName.replace(" ","_")
        sFName=sFName.replace("/","_")
        (fd,filename)=tempfile.mkstemp('.xml','pcs_'+sFName+'_',dir)
        os.close(fd)
        aList.append(filename)
        writePhysicalCardSet(pcs.name,filename)
    return aList

def writeAllPhysicalCardSetsToZip(oZipfile):
    oPhysicalCardSets = PhysicalCardSet.select()
    aList=[];
    for pcs in oPhysicalCardSets:
        sZName=pcs.name
        oW = PhysicalCardSetWriter()
        oString=oW.genDoc(sZName).toprettyxml().encode('utf-8')
        sZName=sZName.replace(" ","_")
        sZName=sZName.replace("/","_")
        sZipName='pcs_'+sZName.encode('ascii','xmlcharrefreplace')+'.xml'
        aList.append(sZipName)
        oZipfile.writestr(sZipName,oString)
    return aList

def readAbstractCardSet(sXmlFile):
    oP = AbstractCardSetParser()
    oP.parse(file(sXmlFile,'rU'))

def writeAbstractCardSet(sAbstractCardSetName,sXmlFile):
    oW = AbstractCardSetWriter()
    if sXmlFile is None:
        filename=sAbstractCardSetName.replace(" ","_") # I hate spaces in filenames
        fOut=file(filename,'w')
    else:
        fOut=file(sXmlFile,'w')
    oW.write(fOut,sAbstractCardSetName)
    fOut.close()

def writeAllAbstractCardSets(dir=''):
    oAbstractCardSets = AbstractCardSet.select()
    aList=[];
    for acs in oAbstractCardSets:
        sFName=acs.name
        sFName=sFName.replace(" ","_")
        sFName=sFName.replace("/","_")
        (fd,filename)=tempfile.mkstemp('.xml','acs_'+sFName+'_',dir)
        os.close(fd)
        aList.append(filename)
        writeAbstractCardSet(acs.name,filename)
    return aList

def writeAllAbstractCardSetsToZip(oZipfile):
    oAbstractCardSets = AbstractCardSet.select()
    aList=[];
    for acs in oAbstractCardSets:
        sZName=acs.name
        oW = AbstractCardSetWriter()
        oString=oW.genDoc(sZName).toprettyxml().encode('utf-8')
        sZName=sZName.replace(" ","_")
        sZName=sZName.replace("/","_")
        sZipName='acs_'+sZName.encode('ascii','xmlcharrefreplace')+'.xml'
        aList.append(sZipName)
        oZipfile.writestr(sZipName,oString)
    return aList


def main(aArgs):
    oOptParser, (oOpts, aArgs) = parseOptions(aArgs)

    if len(aArgs) != 1:
        oOptParser.print_help()
        return 1

    if oOpts.db is None:
        oOpts.db = "sqlite://" + os.path.join(os.getcwd(),"sutekh.db")

    oConn = connectionForURI(oOpts.db)
    sqlhub.processConnection = oConn

    if oOpts.sql_debug:
        oConn.debug = True

    if oOpts.reload:
        if not oOpts.refresh_tables:
            print "reload should be called with --refresh-tables"
            return 1
        else:
            sTempdir=tempfile.mkdtemp('dir','sutekh')
            aPhysicalCardSetList=writeAllPhysicalCardSets(sTempdir)
            aAbstractCardSetList=writeAllAbstractCardSets(sTempdir)
            (fd, sCardList)=tempfile.mkstemp('.xml','physical_cards_',sTempdir)
            # This may not be nessecary, but the available documentation
            # suggests that, on Windows NT anyway, leaving the file open will
            # cause problems when writePhysicalCards tries to reopen it
            os.close(fd)
            writePhysicalCards(sCardList)
            # We dump the databases here
            # We will reload them later

    if oOpts.refresh_ruling_tables:
        if not refreshTables([Ruling],sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_tables:
        if not refreshTables(ObjectList,sqlhub.processConnection):
            print "refresh failed"
            return 1

    if oOpts.refresh_physical_card_tables:
        if not refreshTables([PhysicalCard],sqlhub.processConnection):
            print "refresh failed"
            return 1

    if not oOpts.ww_file is None:
        readWhiteWolfList(oOpts.ww_file)

    if not oOpts.ruling_file is None:
        readRulings(oOpts.ruling_file)

    if not oOpts.read_physical_cards_from is None:
        readPhysicalCards(oOpts.read_physical_cards_from)

    if not oOpts.save_physical_cards_to is None:
        writePhysicalCards(oOpts.save_physical_cards_to)

    if oOpts.save_all_acss and not oOpts.save_acs is None:
        print "Can't use --save-acs and --save-all-acs Simulatenously"
        return 1

    if oOpts.save_all_pcss and not oOpts.save_pcs is None:
        print "Can't use --save-pcs and --save-all-pcs Simulatenously"
        return 1

    if oOpts.save_all_acss:
        writeAllAbstractCardSets()

    if oOpts.save_all_pcss:
        writeAllPhysicalCardSets()

    if oOpts.dump_zip_name is not None:
        oW=PhysicalCardWriter()
        # Zipfile doesn't handle unicode unencoded - blargh
        oString=oW.genDoc().toprettyxml().encode('utf-8')
        oZip=zipfile.ZipFile(oOpts.dump_zip_name,'w')
        oZip.writestr('PhysicalCardList.xml',oString)
        writeAllAbstractCardSetsToZip(oZip)
        writeAllPhysicalCardSetsToZip(oZip)
        oZip.close()

    if oOpts.restore_zip_name is not None:
        oZip=zipfile.ZipFile(oOpts.restore_zip_name,'r')
        bPhysicalCardsRead=False
        # We do this so we can accomodate user created zipfiles,
        # that don't neseecarily have the ordering we want
        for oItem in oZip.infolist():
            sFileName=oItem.filename.split('/')[-1]
            oData=oZip.read(oItem.filename)
            oP=IdentifyXMLFile()
            (sType,sName,bExists)=oP.parseString(oData)
            if sType=='PhysicalCard':
                oP = PhysicalCardParser()
                oP.parseString(oData)
                bPhysicalCardsRead=True
                print "PhysicalCards imported"
                break
        if not bPhysicalCardsRead:
            print "No PhysicalCard list found in the zip file, cannot import"
        else:
            for oItem in oZip.infolist():
                sFileName=oItem.filename.split('/')[-1]
                oData=oZip.read(oItem.filename)
                oP=IdentifyXMLFile()
                (sType,sName,bExists)=oP.parseString(oData)
                if sType=='PhysicalCardSet':
                    oP=PhysicalCardSetParser()
                elif sType=='AbstractCardSet':
                    oP=AbstractCardSetParser()
                else:
                    continue
                oP.parseString(oData)
                print "Imported",sType,sName

    if not oOpts.save_pcs is None:
        writePhysicalCardSet(oOpts.save_pcs,oOpts.pcs_filename)

    if not oOpts.save_acs is None:
        writeAbstractCardSet(oOpts.save_acs,oOpts.acs_filename)

    if not oOpts.read_pcs is None:
        readPhysicalCardSet(oOpts.read_pcs)

    if not oOpts.read_acs is None:
        readAbstractCardSet(oOpts.read_acs)

    if oOpts.reload:
        readPhysicalCards(sCardList)
        os.remove(sCardList)
        for pcs in aPhysicalCardSetList:
            readPhysicalCardSet(pcs)
            os.remove(pcs)
        for acs in aAbstractCardSetList:
            readAbstrctCardSet(acs)
            os.remove(acs)
        os.rmdir(sTempdir)

    if oOpts.upgrade_db and oOpts.refresh_tables:
        print "Can't use --upgrade-db and --refresh-tables simulatenously"
        return 1
 
    if oOpts.upgrade_db:
        attemptDatabaseUpgrade()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
