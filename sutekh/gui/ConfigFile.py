# ConfigFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Config handling object
# Wrapper around configobj and validate with some hooks for Sutekh purposes
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

"""Configuration handling for the Sutekh GUI."""

from configobj import ConfigObj, flatten_errors
from validate import Validator, is_option, is_list
import pkg_resources
import weakref

# Type definitions
CARDSET = 'Card Set'
FRAME = 'Frame'
WW_CARDLIST = 'cardlist'
CARDSET_LIST = 'cardset list'


def is_option_list(sValue, *aOptions):
    """Validator function for option_list configspec type."""
    return [is_option(sMem, *aOptions) for sMem in is_list(sValue)]


class ConfigFileListener(object):
    """Listener object for config changes - inspired by CardListModeListener"""

    def add_filter(self, sKey, sFilter):
        """New Filter added"""
        pass

    def remove_filter(self, sKey, sFilter):
        """Filter removed"""
        pass

    def replace_filter(self, sKey, sOldFilter, sNewFilter):
        """A Filter has been replaced"""
        pass

    def set_postfix_the_display(self, bPostfix):
        """Postfix display mode has been set."""
        pass

    def profile_option_changed(self, sType, sProfile, sKey):
        """One of the profile configuration items changed."""
        pass

    def profile_changed(self, sType, sId):
        """The profile associated with a cardset changed."""
        pass

    def remove_profile(self, sType, sProfile):
        """A profile has been removed"""
        pass


class ConfigFile(object):
    """Handle the setup and management of the config file.

       Ensure that the needed sections exist, and that sensible
       defaults values are assigned.

       Filters are saved to the config file, and interested objects
       can register as listeners on the config file to respond to
       changes to the filters.
       """
    # pylint: disable-msg=R0904, R0902
    # R0904 - We need to provide fine-grained access to all the data,
    # so lots of methods
    # R0902 - Lots of internal state, so lots of attributes

    dCustomConfigTypes = {
        'option_list': is_option_list,
    }

    def __init__(self, sFileName):
        self.__sFileName = sFileName
        self.__bWriteable = False
        self.__oConfigSpec = None
        self.__oConfig = None
        self.__dLocalFrameOptions = {}
        self.__oValidator = None
        # allow listeners to be automatically removed by garbage
        # collection
        self.__dListeners = weakref.WeakKeyDictionary()
        self.__dPluginSpecs = {}
        self.__dDeckSpecs = {}
        self.__dCardListSpecs = {}
        self.__dCardSetListSpecs = {}

    def __str__(self):
        """Debugging aid - include the filename"""
        return "<%s object at %s; config file: %r>" % (
            self.__class__.__name__, hex(id(self)), self.__sFileName)

    def add_listener(self, oListener):
        """Add a listener to respond to config file changes."""
        self.__dListeners[oListener] = None

    def remove_listener(self, oListener):
        """Remove a listener from the list."""
        del self.__dListeners[oListener]

    def listeners(self):
        """Return a list of listeners.

        Useful for iterating over the listeners since the internal
        list is stored in a weakref dictionary.
        """
        return self.__dListeners.keys()

    def add_plugin_specs(self, sName, dConfigSpecs):
        """Add a validator to the plugins_main configspec section."""
        self.__dPluginSpecs[sName] = dConfigSpecs

    def add_deck_specs(self, sName, dConfigSpecs):
        """Add validation options to the per_deck.defaults configspec."""
        self.__dDeckSpecs[sName] = dConfigSpecs

    def add_cardlist_specs(self, sName, dConfigSpecs):
        """Add validation options to the cardlist configspec."""
        self.__dCardListSpecs[sName] = dConfigSpecs

    def add_cardset_list_specs(self, sName, dConfigSpecs):
        """Add validation options to the cardset list configspec."""
        self.__dCardSetListSpecs[sName] = dConfigSpecs

    def validate(self):
        """Validate a configuration object."""
        # pylint: disable-msg=E1101
        # pkg_resources confuses pylint here
        fConfigSpec = pkg_resources.resource_stream(__name__, "configspec.ini")
        oConfigSpec = ConfigObj(fConfigSpec, raise_errors=True,
                file_error=True, list_values=False)

        for sPlugin, dGlobal in self.__dPluginSpecs.items():
            oConfigSpec['plugins_main'][sPlugin] = dGlobal

        for sPlugin, dPerDeck in self.__dDeckSpecs.items():
            for sKey, oValue in dPerDeck.items():
                oConfigSpec['per_deck']['defaults'][sKey] = oValue

        for sPlugin, dGlobal in self.__dCardListSpecs.items():
            for sKey, oValue in dGlobal.items():
                oConfigSpec['cardlist']['defaults'][sKey] = oValue

        for sPlugin, dGlobal in self.__dCardSetListSpecs.items():
            for sKey, oValue in dGlobal.items():
                oConfigSpec['cardset list']['defaults'][sKey] = oValue

        # Set __many__ sections to match defaults sections, so validation
        # does the value conversion for us

        for sKey, oValue in oConfigSpec['cardlist']['defaults'].items():
            oConfigSpec['cardlist']['profiles']['__many__'][sKey] = oValue
        for sKey, oValue in oConfigSpec['cardset list']['defaults'].items():
            oConfigSpec['cardset list']['profiles']['__many__'][sKey] = oValue
        for sKey, oValue in oConfigSpec['per_deck']['defaults'].items():
            oConfigSpec['per_deck']['profiles']['__many__'][sKey] = oValue

        self.__oConfigSpec = oConfigSpec
        self.__oConfig = ConfigObj(self.__sFileName, configspec=oConfigSpec,
                indent_type='    ')
        self.__oValidator = Validator(self.dCustomConfigTypes)

        oResults = self.__oConfig.validate(self.__oValidator,
                preserve_errors=True)
        return oResults

    def validation_errors(self, oValidationResults):
        """Return a list of string describing any validation errors.

           Returns an empty list if no validation errors occurred. Validation
           results must have been returned by a call to validate() on the same
           config object.
           """
        aErrors = []
        if oValidationResults == True:
            return aErrors

        for (aSections, sKey, _oIgnore) in flatten_errors(self.__oConfig,
            oValidationResults):
            if sKey is not None:
                aErrors.append('Key %r in section %r failed validation.' %
                        (sKey, aSections))
            else:
                aErrors.append('Section %r was missing.' % (aSections,))

        return aErrors

    def get_validator(self):
        """Return the validator used to check the configuration."""
        return self.__oValidator

    def sanitize(self):
        """Called after validation to clean up a valid config.

           Currently clean-up consists of adding some open panes if none
           are listed.
           """
        if not self.__oConfig['open_frames']:
            # No panes information, so we set 'sensible' defaults
            self.add_frame(1, 'physical_card', 'White Wolf Card List', False,
                    False, -1, None)
            self.add_frame(2, 'Card Text', 'Card Text', False, False, -1, None)
            self.add_frame(3, 'Card Set List', 'Card Set List', False, False,
                    -1, None)
            self.add_frame(4, 'physical_card_set', 'My Collection', False,
                    False, -1, None)

    def check_writeable(self):
        """Test that we can open the file for writing"""
        self.__bWriteable = True
        try:
            oFile = open(self.__sFileName, 'a')
            oFile.close()
        except IOError:
            self.__bWriteable = False
        return self.__bWriteable

    def write(self):
        """Write the config file to disk."""
        if self.__bWriteable:
            self.__oConfig.write()

    #
    # Open Frame Handling
    #

    def clear_open_frames(self):
        """Clear out old save panes (used before adding new ones)."""
        self.__oConfig['open_frames'].clear()

    def open_frames(self):
        """Get the all the panes saved in the config file, and their
           positions."""
        aRes = []
        for sKey, dPane in self.__oConfig['open_frames'].items():
            if not sKey.startswith('pane'):
                # invalid key
                continue
            try:
                iPaneNumber = int(sKey.split(' ')[1])
            except ValueError:
                # invalid key
                continue

            iPos = dPane['position']
            if dPane['orientation'] == 'C':
                # We aim for minimal impact on the layout of other panes
                iPos = 0

            aRes.append((
                iPaneNumber,
                dPane['type'],
                dPane['name'],
                dPane['paneid'],
                dPane['orientation'] == 'V',
                dPane['orientation'] == 'C',
                iPos,
            ))

        aRes.sort()  # Numbers denote ordering
        return aRes

    def update_pane_numbers(self, dPaneMap):
        """Update the profiles to reflect changes in pane-id.

           dPaneMap is a dictionary mapping old_id -> new_id"""
        # We use a copy, so we avoid problems where sNewId is equal to
        # a later sOldId
        dOldProfiles = self.__oConfig['per_deck']['frame_profiles'].copy()
        # Clear old state, ensuring we set any botched loads to the
        # default profile
        for sId in dOldProfiles:
            self.set_profile(FRAME, sId, None)
        for sOldId, sNewId in dPaneMap.iteritems():
            if sOldId in dOldProfiles:
                # use set_profile to ensure we call the listeners
                self.set_profile(FRAME, sNewId, dOldProfiles[sOldId])

    # pylint: disable-msg=R0913
    # We need all the info in the arguments here
    def add_frame(self, iFrameNumber, sType, sName, bVertical, bClosed, iPos,
            sPaneId):
        """Add a frame with the given position info to the config file"""
        oPanes = self.__oConfig['open_frames']
        sKey = 'pane %d' % iFrameNumber

        oPanes[sKey] = {}
        oNewPane = oPanes[sKey]

        oNewPane['type'] = sType
        oNewPane['name'] = sName
        oNewPane['paneid'] = sPaneId

        if bVertical:
            oNewPane['orientation'] = "V"
        elif bClosed:
            oNewPane['orientation'] = "C"
        else:
            oNewPane['orientation'] = "H"

        if iPos > 0 and self.get_save_precise_pos() and not bClosed:
            oNewPane['position'] = iPos
        elif bClosed:
            oNewPane['position'] = 0
        else:
            oNewPane['position'] = -1

    # pylint: enable-msg=R0913

    #
    # Plugin Config Section Handling
    #

    def get_plugin_key(self, sPlugin, sKey):
        """Get an option from the plugins section.

           Return None if no option is set
           """
        try:
            sResult = self.__oConfig['plugins_main'][sPlugin][sKey]
        except KeyError:
            sResult = None
        return sResult

    def set_plugin_key(self, sPlugin, sKey, sValue, bCreateSection=False):
        """Set a value in the plugin section"""
        if bCreateSection and sPlugin not in self.__oConfig['plugins_main']:
            self.__oConfig['plugins_main'][sPlugin] = {}
        self.__oConfig['plugins_main'][sPlugin][sKey] = sValue

    #
    # Filters section
    #

    def get_filters(self):
        """Get all the filters in the config file.

           Filters are return as a list of (sQuery, dVars) tuples.
           """
        return [(oF['query'], oF['vars']) for oF in
            self.__oConfig['filters'].values()]

    def get_filter_keys(self):
        """Return all the keys for all the filters in the config file."""
        return [(sKey, dFilter['query']) for sKey, dFilter in
            self.__oConfig['filters'].items()]

    def get_filter(self, sKey):
        """Return the filter associated with the given key.

           Return None if the filter is not known.
           """
        sKey = sKey.lower()
        if sKey in self.__oConfig['filters']:
            return self.__oConfig['filters'][sKey]['query']
        else:
            return None

    def get_filter_values(self, sKey):
        """Return the filter values associated with the given key.

        Return None if the filter is not knonw.
        """
        sKey = sKey.lower()
        if sKey in self.__oConfig['filters']:
            return self.__oConfig['filters'][sKey]['vars'].dict()
        else:
            return None

    # pylint: disable-msg=W0102
    # W0102 - {} is the right thing here
    def add_filter(self, sKey, sQuery, dVars={}):
        """Add a filter to the config file."""
        sKey = sKey.lower()
        if sKey not in self.__oConfig['filters']:
            dFilter = {
                'query': sQuery,
                'vars': dVars,
            }
            self.__oConfig['filters'][sKey] = dFilter
            for oListener in self.listeners():
                oListener.add_filter(sKey, sQuery)

    # pylint: enable-msg=W0102

    def remove_filter(self, sKey, sFilter):
        """Remove a filter from the file"""
        # Make sure Filer and key match
        sKey = sKey.lower()
        if sKey in self.__oConfig['filters'] and \
                sFilter == self.__oConfig['filters'][sKey]['query']:
            del self.__oConfig['filters'][sKey]
            for oListener in self.listeners():
                oListener.remove_filter(sKey, sFilter)

    def replace_filter(self, sKey, sOldFilter, sNewFilter):
        """Replace a filter in the file with new filter"""
        sKey = sKey.lower()
        if sKey in self.__oConfig['filters'] and \
                sOldFilter == self.__oConfig['filters'][sKey]['query']:
            self.__oConfig['filters'][sKey]['query'] = sNewFilter
            for oListener in self.listeners():
                oListener.replace_filter(sKey, sOldFilter, sNewFilter)

    #
    # Per-Deck Options
    #

    def get_deck_option(self, sFrame, sCardset, sKey, bUseLocal=True):
        """Retrieve the value of a per-deck option.

           Either sFrame or sCardset may be None, in
           which case the frame or cardset option look-up
           is skipped.
           """
        try:
            if bUseLocal:
                return self.__dLocalFrameOptions[sFrame][sKey]
        except KeyError:
            pass

        dPerDeck = self.__oConfig['per_deck']

        try:
            sProfile = dPerDeck['frame_profiles'][sFrame]
            return dPerDeck['profiles'][sProfile][sKey]
        except KeyError:
            pass

        try:
            sProfile = dPerDeck['cardset_profiles'][sCardset]
            return dPerDeck['profiles'][sProfile][sKey]
        except KeyError:
            pass

        return dPerDeck['defaults'][sKey]

    def get_deck_profile_option(self, sProfile, sKey):
        """Get the value of a per-deck option for a profile."""
        try:
            if sProfile is None:
                return self.__oConfig['per_deck']['defaults'][sKey]
            else:
                return self.__oConfig['per_deck']['profiles'][sProfile][sKey]
        except KeyError:
            return None

    def get_local_frame_option(self, sFrame, sKey):
        """Get the value of a per-deck option for a local frame."""
        try:
            return self.__dLocalFrameOptions[sFrame][sKey]
        except KeyError:
            return None

    def set_profile_option(self, sType, sProfile, sKey, sValue):
        """Set the value of a option for a profile for sType.

           If sValue is None, remove the key. New profiles are
           created as needed.
           """
        if sType == CARDSET:
            dConfig = self.__oConfig['per_deck']
        else:
            dConfig = self.__oConfig[sType]
        if sProfile is None:
            dProfile = dConfig['defaults']
        elif sProfile in dConfig['profiles']:
            dProfile = dConfig['profiles'][sProfile]
        else:
            # configobj replaces the dict with a config object, so
            # trigger the creation of the config object, then set
            # dProfile to it
            dConfig['profiles'][sProfile] = {}
            dProfile = dConfig['profiles'][sProfile]

        bChanged = False
        if sValue is None:
            if sKey in dProfile:
                bChanged = True
                del dProfile[sKey]
        else:
            if sKey not in dProfile or dProfile[sKey] != sValue:
                bChanged = True
                dProfile[sKey] = sValue

        if bChanged:
            for oListener in self.listeners():
                oListener.profile_option_changed(sType, sProfile, sKey)

    def set_local_frame_option(self, sFrame, sKey, sValue):
        """Set the value of an option in the local frame option dictionary.

        If sValue is None, remove the key.
        """
        if sFrame in self.__dLocalFrameOptions:
            dOptions = self.__dLocalFrameOptions[sFrame]
        else:
            dOptions = {}
            self.__dLocalFrameOptions[sFrame] = dOptions

        bChanged = False
        if sValue is None:
            if sKey in dOptions:
                bChanged = True
                del dOptions[sKey]
        else:
            if sKey not in dOptions or dOptions[sKey] != sValue:
                bChanged = True
                dOptions[sKey] = sValue

        if bChanged:
            for oListener in self.listeners():
                oListener.profile_changed(FRAME, sFrame)

    def clear_frame_profile(self, sId):
        """Clear any pane profiles set for this frame"""
        dProfiles = self.__oConfig['per_deck']['frame_profiles']
        if sId in dProfiles:
            # We should only be called while the pane is being closed,
            # so we don't notify the listeners to avoid causing a
            # pointless reload.
            del dProfiles[sId]

    def clear_cardset_profile(self, sId):
        """Clear any profiles set for this cardset"""
        # We don't need to worry about the pane profiles, as the
        # the frames will be explicitly closed, which will take care of those
        # for us.
        dProfiles = self.__oConfig['per_deck']['cardset_profiles']
        if sId in dProfiles:
            # We should only be called while the pane is being closed,
            # so we don't notify the listeners to avoid causing a
            # pointless reload.
            del dProfiles[sId]

    def fix_profile_mapping(self, dOldMap, dNewMap):
        """Update the card set profiles to a new id -> name mapping"""
        # We need to reverse of dNewMapping. Since both name and id are
        # unique, this is safe
        dNewRev = dict(zip(dNewMap.itervalues(), dNewMap.iterkeys()))
        dOldProfiles = self.__oConfig['per_deck']['cardset_profiles'].copy()
        dProfiles = self.__oConfig['per_deck']['cardset_profiles']
        dProfiles.clear()
        for sId, sProfile in dOldProfiles.iteritems():
            iId = int(sId[2:])  # cs<cardset id>
            if iId not in dOldMap:
                # ini file out of synce with database, so skip this entry
                # (lots of ways this can happen - sutekh-cli, editing, etc.)
                continue
            sName = dOldMap[iId]
            if sName in dNewRev:
                sNewId = 'cs%d' % dNewRev[sName]
                dProfiles[sNewId] = sProfile

    def set_profile(self, sType, sId, sProfile):
        """Set the profile associated of the given type."""
        if sType == CARDSET or sType == FRAME:
            if sType == CARDSET:
                dProfiles = self.__oConfig['per_deck']['cardset_profiles']
            else:
                dProfiles = self.__oConfig['per_deck']['frame_profiles']
            if dProfiles.get(sId) == sProfile:
                return
            if sProfile is None:
                del dProfiles[sId]
            else:
                dProfiles[sId] = sProfile
        elif (sType == WW_CARDLIST and sId == WW_CARDLIST) or \
                (sType == CARDSET_LIST and sId == CARDSET_LIST):
            sCurProfile = self.__oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                return
            if sProfile is None:
                del self.__oConfig[sType]['current profile']
            else:
                self.__oConfig[sType]['current profile'] = sProfile
        else:
            # Unrecognised type / cardset combo
            return
        for oListener in self.listeners():
            oListener.profile_changed(sType, sId)

    def get_profile(self, sType, sId):
        """Return the current profile of the cardset/cardlist/cardset list."""
        if sType == CARDSET:
            return self.__oConfig['per_deck']['cardset_profiles'].get(sId)
        elif sType == FRAME:
            return self.__oConfig['per_deck']['frame_profiles'].get(sId)
        elif (sType == WW_CARDLIST and sId == WW_CARDLIST) or \
                (sType == CARDSET_LIST and sId == CARDSET_LIST):
            return self.__oConfig[sType].get('current profile')
        return None

    def clear_profiles(self, sType, sProfile):
        """Find all cardsets/frames using this profile, and change them to
          the default"""
        if sType == CARDSET or sType == FRAME:
            if sType == CARDSET:
                dProfiles = self.__oConfig['per_deck']['cardset_profiles']
            else:
                dProfiles = self.__oConfig['per_deck']['frame_profiles']
            # Loop over a copy, as we may change the dict
            for sId, sCurProfile in dProfiles.items():
                if sCurProfile == sProfile:
                    self.set_profile(sType, sId, None)
        else:
            sCurProfile = self.__oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                self.set_profile(sType, sType, None)

    def remove_profile(self, sType, sProfile):
        """Remove a profile from the file"""
        dData = {}
        if sType == FRAME or sType == CARDSET:
            dData = self.__oConfig['per_deck']['profiles']
        elif sType == CARDSET_LIST:
            dData = self.__oConfig['cardset list']['profiles']
        elif sType == WW_CARDLIST:
            dData = self.__oConfig['cardlist']['profiles']
        if sProfile in dData:
            if sType == FRAME or sType == CARDSET:
                # Need to clear both lists in this case
                self.clear_profiles(FRAME, sProfile)
                self.clear_profiles(CARDSET, sProfile)
            else:
                self.clear_profiles(sType, sProfile)
            del dData[sProfile]
            for oListener in self.listeners():
                oListener.remove_profile(sType, sProfile)

    def frame_profiles(self):
        """Return a dictionary of frame id -> profile mappings."""
        return dict(self.__oConfig['per_deck']['frame_profiles'])

    def get_profile_users(self, sType, sProfile):
        """Returns a list of all card sets or panes that use the
           given profile"""
        if sType == CARDSET_LIST:
            sCurProfile = self.__oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                return ['Card Set List']
        elif sType == WW_CARDLIST:
            sCurProfile = self.__oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                return ['White Wolf Card List']
        elif sType == CARDSET:
            aUsers = []
            for dProfiles in (
                    self.__oConfig['per_deck']['cardset_profiles'],
                    self.__oConfig['per_deck']['frame_profiles'],
                    ):
                for sId, sCurProfile in dProfiles.iteritems():
                    if sProfile == sCurProfile:
                        aUsers.append(sId)
            return aUsers
        return None

    def profiles(self, sType):
        """Return a list of profile keys."""
        if sType == FRAME or sType == CARDSET:
            return list(self.__oConfig['per_deck']['profiles'].keys())
        elif sType == CARDSET_LIST:
            return list(self.__oConfig['cardset list']['profiles'].keys())
        elif sType == WW_CARDLIST:
            return list(self.__oConfig['cardlist']['profiles'].keys())
        # Unkown type
        return None

    def profile_options(self, sType):
        """Return a list of per-deck option names."""
        if sType == FRAME or sType == CARDSET:
            return self.__oConfig['per_deck']['defaults'].keys()
        return self.__oConfig[sType]['defaults'].keys()

    def get_option_spec(self, sType, sKey):
        """Return the config spec for a given option."""
        if sType == FRAME or sType == CARDSET:
            return self.__oConfigSpec['per_deck']['defaults'][sKey]
        return self.__oConfigSpec[sType]['defaults'][sKey]

    def get_profile_option(self, sType, sProfile, sKey):
        """Get the value of a per-deck option for a profile."""
        if sType == FRAME or sType == CARDSET:
            return self.get_deck_profile_option(sProfile, sKey)
        try:
            if sProfile is None or sProfile.lower() == "default":
                return self.__oConfig[sType]['defaults'][sKey]
            else:
                # We fall back to the defaults if the key isn't set yet
                try:
                    return self.__oConfig[sType]['profiles'][sProfile][sKey]
                except KeyError:
                    return self.__oConfig[sType]['defaults'][sKey]
        except KeyError:
            return None

    #
    # Application Level Config Settings
    #

    def get_save_on_exit(self):
        """Query the 'save on exit' option."""
        return self.__oConfig['main']['save on exit']

    def set_save_on_exit(self, bSaveOnExit):
        """Set the 'save on exit' option."""
        self.__oConfig['main']['save on exit'] = bSaveOnExit

    def get_save_precise_pos(self):
        """Query the 'save pane sizes' option."""
        return self.__oConfig['main']['save pane sizes']

    def set_save_precise_pos(self, bSavePos):
        """Set the 'save pane sizes' option."""
        self.__oConfig['main']['save pane sizes'] = bSavePos

    def get_save_window_size(self):
        """Query the 'save window size' option."""
        return self.__oConfig['main']['save window size']

    def set_save_window_size(self, bSavePos):
        """Set the 'save window size' option."""
        self.__oConfig['main']['save window size'] = bSavePos

    def set_database_uri(self, sDatabaseURI):
        """Set the configured database URI"""
        self.__oConfig['main']['database url'] = sDatabaseURI

    def get_database_uri(self):
        """Get database URI from the config file"""
        return self.__oConfig['main']['database url']

    def get_icon_path(self):
        """Get the icon path from the config file"""
        return self.__oConfig['main']['icon path']

    def set_icon_path(self, sPath):
        """Set the configured icon path"""
        self.__oConfig['main']['icon path'] = sPath

    def get_window_size(self):
        """Get the saved window size from the config file."""
        iWidth, iHeight = self.__oConfig['main']['window size']
        return iWidth, iHeight

    def set_window_size(self, tSize):
        """Save the current window size."""
        self.__oConfig['main']['window size'] = tSize

    def get_postfix_the_display(self):
        """Get the 'postfix name display' option."""
        return self.__oConfig['main']['postfix name display']

    def set_postfix_the_display(self, bPostfix):
        """Set the 'postfix name display' option."""
        self.__oConfig['main']['postfix name display'] = bPostfix
        for oListener in self.listeners():
            oListener.set_postfix_the_display(bPostfix)
