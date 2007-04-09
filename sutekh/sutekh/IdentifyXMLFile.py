# IdentifyXMLFile.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Modifications copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Attempts to identify a XML file as either PhysicalCard, PhysicalCardSet or
AbstractCardSet
"""

from sutekh.SutekhObjects import AbstractCardSet, PhysicalCardSet, PhysicalCard
from sqlobject import SQLObjectNotFound
from xml.sax import parse,_exceptions,parseString
from xml.sax.handler import ContentHandler

class IdentifyXMLHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.sType='Unknown'
        self.sName=None
        self.bExists=False

    def startElement(self,sTagName,oAttrs):
        if sTagName == 'abstractcardset':
            self.sType='AbstractCardSet'
            self.sName = oAttrs.getValue('name')
            try:
                acs=AbstractCardSet.byName(self.sName.encode('utf8'))
                self.bExists=True
            except SQLObjectNotFound:
                self.bExists=False
        if sTagName == 'physicalcardset':
            self.sType='PhysicalCardSet'
            self.sName = oAttrs.getValue('name')
            try:
                acs=PhysicalCardSet.byName(self.sName.encode('utf8'))
                self.bExists=True
            except SQLObjectNotFound:
                self.bExists=False
        if sTagName == 'cards':
            self.sType='PhysicalCard'
            # There is only 1 PhysicalCard List, so it exists if it's
            # not empty
            self.bExists=PhysicalCard.select().count()>0

    def endElement(self,sName):
        pass

    def getDetails(self):
        return (self.sType,self.sName,self.bExists)

class IdentifyXMLFile(object):
    def parse(self,fIn):
        myHandler=IdentifyXMLHandler()
        try:
            parse(fIn,myHandler)
        except _exceptions.SAXParseException:
            pass
        return myHandler.getDetails()

    def parseString(self,sIn):
        myHandler=IdentifyXMLHandler()
        try:
            parseString(sIn,myHandler)
        except _exceptions.SAXParseException:
            pass
        return myHandler.getDetails()
