# PhysicalCardMappingHolder.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""
Handle mapping between PhysicalCards and PhysicalCardSets.
Useful for database upgrades and restoring from backups.
"""

from sutekh.core.SutekhObjects import AbstractCard, PhysicalCardSet, \
        PhysicalCard, MapPhysicalCardToPhysicalCardSet, IExpansion
try:
    from xml.etree.ElementTree import Element, SubElement, tostring, fromstring
except ImportError:
    from elementtree.ElementTree import Element, SubElement, tostring, \
            fromstring

class PhysicalCardMappingHolder(object):
    """
    Object to store the Mapping between the Physical Cards and the 
    Physical Card Sets. Uses elementtree for easy export to XML for
    backups.
    """

    sUnknown = 'Unspecified Expansion'

    def __init__(self):
        "Constructor"
        self.oMapping = None

    def __remap_names(self, sString):
        """
        Remap a card or expansion name to an acceptable tag
        """
        # Tags can't have spaces or punctation
        import string
        sResult = sString.replace(' ', '').encode('ascii','xmlcharrefreplace')
        for sChar in string.punctuation:
            sResult = sResult.replace(sChar, '')
        if sResult[0] in string.digits:
            sResult = 'a' + sResult # 44 Magnum triggers this
        return sResult

    def fill_from_db(self, oConnection):
        """
        Create an ElementTree describing the mapping between the physical cards
        and the physical card sets from the database.
        """
        # We could do this using a multi-layer dict, but the ElementTree has
        # more structure, and is also useful for the backup system
        self.oMapping = Element('cardmapping')
        for oCard in PhysicalCard.select(connection=oConnection):
            sTagName = self.__remap_names(oCard.abstractCard.canonicalName)
            oCardNode = self.oMapping.find(sTagName)
            if oCardNode is None:
                oCardNode = SubElement(self.oMapping, sTagName)
                oCardNode.attrib['cardname'] = oCard.abstractCard.canonicalName
            if oCard.expansion is None:
                sExpansionName = self.sUnknown
            else:
                sExpansionName = oCard.expansion.name
            oExpansionNode = oCardNode.find(self.__remap_names(sExpansionName))
            if oExpansionNode is None:
                oExpansionNode = SubElement(oCardNode,
                        self.__remap_names(sExpansionName))
                oExpansionNode.attrib['name'] = sExpansionName
            # Tag can't be all numbers, or fromstring will break
            oIdNode = SubElement(oExpansionNode, 'a' + str(oCard.id))
            # Find the physical card sets this card belongs to
            for oMPCS in MapPhysicalCardToPhysicalCardSet.selectBy(
                    physicalCardID=oCard.id, connection=oConnection):
                oPCS = oMPCS.physicalCardSet
                oPCSNode = SubElement(oIdNode, self.__remap_names(oPCS.name))
                oPCSNode.attrib['name'] = oPCS.name

    def fill_from_string(self, sXMLString):
        """
        Parse the XML string into the mapping structure
        """
        self.oMapping = fromstring(sXMLString)

    def get_string(self):
        """
        Get the XML String representation of the ElementTree.
        """
        if self.oMapping:
            return tostring(self.oMapping)
        else:
            return ''

    def commit_to_db(self, oConnection, dCardLookupCache={}):
        """
        Commit the mapping to the database.
        Use dLookupCache to handle any changed card names (on DB upgrade).
        Return True if successful, false on error conditions
        """
        if self.oMapping is None:
            return False
        for oCardNode in self.oMapping:
            for oExpansionNode in oCardNode:
                # If we only have 1 of the card & expansion, then
                # the mapping is trivially correct
                if len(oExpansionNode) == 1:
                    continue
                # Get current database information
                if oCardNode.attrib['cardname'] in dCardLookupCache:
                    sCardName = dCardLookupCache[oCardNode.attrib['cardname']]
                else:
                    sCardName = oCardNode.attrib['cardname']
                oAC = list(AbstractCard.selectBy(canonicalName=sCardName,
                        connection=oConnection))
                sExpansionName = oExpansionNode.attrib['name']
                if sExpansionName == self.sUnknown:
                    oExpID = None
                else:
                    oExpID = IExpansion(sExpansionName).id
                aPhysicalCards = list(PhysicalCard.selectBy(
                    abstractCardID=oAC[0].id,
                    expansionID=oExpID, connection=oConnection))
                if len(aPhysicalCards) != len(oExpansionNode):
                    return False # Error Condition
                for oIdNode, oPC in zip(oExpansionNode, aPhysicalCards):
                    aMap = MapPhysicalCardToPhysicalCardSet.selectBy(
                            physicalCardID=oPC.id, connection=oConnection)
                    aPCS = [x.physicalCardSet for x in aMap]
                    aNames = [x.name for x in aPCS]
                    for oPCSNode in oIdNode:
                        if oPCSNode.attrib['name'] not in aNames:
                            # Missing PCS, so add card to this PCS
                            oPCS = list(PhysicalCardSet.selectBy(
                                    name=oPCSNode.attrib['name'],
                                    connection=oConnection))[0]
                            oPCS.addPhysicalCard(oPC.id)
                    for oPCS in aPCS:
                        if oIdNode.find(self.__remap_names(oPCS.name)) is None:
                            # Extra one, so delete card from this PCS
                            oPCS.removePhysicalCard(oPC.id)
        return True
