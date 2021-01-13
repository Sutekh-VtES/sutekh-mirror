# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Config handling object
# Wrapper around configobj and validate with some hooks for Sutekh purposes
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

"""Base classes and constants for configuation management."""

import datetime

import pkg_resources
from configobj import ConfigObj, flatten_errors
from validate import Validator, is_option, is_list, VdtTypeError

from .MessageBus import MessageBus

# Type definitions
CARDSET = 'Card Set'
FRAME = 'Frame'
FULL_CARDLIST = 'cardlist'
CARDSET_LIST = 'cardset list'

# Reserved filter names (for filter in profile special cases)
DEF_PROFILE_FILTER = 'No profile filter'


def is_option_list(sValue, *aOptions):
    """Validator function for option_list configspec type."""
    return [is_option(sMem, *aOptions) for sMem in is_list(sValue)]


def is_date_format(sValue):
    """Validator function to check for date format."""
    try:
        oDate = datetime.datetime.strptime(sValue, '%Y-%m-%d').date()
    except ValueError:
        raise VdtTypeError(sValue)
    return oDate


class BaseConfigFile:
    """Handle the setup and management of the config file.

       Ensure that the needed sections exist, and that sensible
       defaults values are assigned.

       Filters are saved to the config file, and interested objects
       can register as listeners on the config file to respond to
       changes to the filters.
       """
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    # We need to provide fine-grained access to all the data,
    # so lots of methods
    # Lots of internal state, so lots of attributes

    dCustomConfigTypes = {
        'option_list': is_option_list,
        'date': is_date_format,
    }

    # Subclasses should specify the correct thing here
    DEFAULT_FILTERS = {}

    def __init__(self, sFileName):
        self._sFileName = sFileName
        self._bWriteable = False
        self._oConfigSpec = None
        self._oConfig = None
        self._dLocalFrameOptions = {}
        self._oValidator = None
        self._dPluginSpecs = {}
        self._dDeckSpecs = {}
        self._dCardListSpecs = {}
        self._dCardSetListSpecs = {}

    def __str__(self):
        """Debugging aid - include the filename"""
        return "<%s object at %s; config file: %r>" % (
            self.__class__.__name__, hex(id(self)), self._sFileName)

    def add_plugin_specs(self, sName, dConfigSpecs):
        """Add a validator to the plugins_main configspec section."""
        self._dPluginSpecs[sName] = dConfigSpecs

    def add_deck_specs(self, sName, dConfigSpecs):
        """Add validation options to the per_deck.defaults configspec."""
        self._dDeckSpecs[sName] = dConfigSpecs

    def add_cardlist_specs(self, sName, dConfigSpecs):
        """Add validation options to the cardlist configspec."""
        self._dCardListSpecs[sName] = dConfigSpecs

    def add_cardset_list_specs(self, sName, dConfigSpecs):
        """Add validation options to the cardset list configspec."""
        self._dCardSetListSpecs[sName] = dConfigSpecs

    def _get_app_configspec_file(self):
        """Get the application specific config spec file.

           Return None if there's no extension to the base configspec"""
        # Subclasses should provide this
        raise NotImplementedError

    def validate(self):
        """Validate a configuration object."""
        fConfigSpec = pkg_resources.resource_stream(__name__,
                                                    "baseconfigspec.ini")
        oConfigSpec = ConfigObj(fConfigSpec, raise_errors=True,
                                file_error=True, list_values=False,
                                encoding='utf8')

        fAppConfigSpec = self._get_app_configspec_file()
        if fAppConfigSpec:
            oAppConfigSpec = ConfigObj(fAppConfigSpec, raise_errors=True,
                                       file_error=True, list_values=False,
                                       encoding='utf8')
            # Merge overrides from the application
            oConfigSpec.merge(oAppConfigSpec)
            fAppConfigSpec.close()
        fConfigSpec.close()

        for sPlugin, dGlobal in self._dPluginSpecs.items():
            oConfigSpec['plugins_main'][sPlugin] = dGlobal

        for sPlugin, dPerDeck in self._dDeckSpecs.items():
            for sKey, oValue in dPerDeck.items():
                oConfigSpec['per_deck']['defaults'][sKey] = oValue

        for sPlugin, dGlobal in self._dCardListSpecs.items():
            for sKey, oValue in dGlobal.items():
                oConfigSpec['cardlist']['defaults'][sKey] = oValue

        for sPlugin, dGlobal in self._dCardSetListSpecs.items():
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

        self._oConfigSpec = oConfigSpec
        self._oConfig = ConfigObj(self._sFileName, configspec=oConfigSpec,
                                  indent_type='    ',
                                  encoding='utf8')
        # We do this before validation, so validation will flag errors
        # for us
        self.update_filter_list()
        self._oValidator = Validator(self.dCustomConfigTypes)

        oResults = self._oConfig.validate(self._oValidator,
                                          preserve_errors=True)

        # It's OK to do this after validation, since this is only
        # to catch the case when filter entries have not been set yet,
        # which don't cause a validation error.
        self._fix_filter_defaults()

        return oResults

    def update_filter_list(self):
        """Add/Update a option validator for the filters.

           This is so the profile editor lists things sensibly."""
        try:
            aValidProfileFilters = self._oConfig['filters'].keys()
        except KeyError:
            aValidProfileFilters = []
        aValidProfileFilters.append(DEF_PROFILE_FILTER)
        # We set this directly on the spec object, since we need to
        # override the existing value whenever the filter list changes
        for sType in ['per_deck', FULL_CARDLIST]:
            self._oConfigSpec[sType]['defaults']['filter'] = \
                "option(%s, default=%s)" % (", ".join(aValidProfileFilters),
                                            DEF_PROFILE_FILTER)
            # Also add to the __many__ section
            self._oConfigSpec[sType]['profiles']['__many__']['filter'] = \
                "option(%s, default=%s)" % (", ".join(aValidProfileFilters),
                                            DEF_PROFILE_FILTER)

    def _fix_filter_defaults(self):
        """Ensure we are set in the default profile if needed"""
        for sType in ['per_deck', FULL_CARDLIST]:
            if 'filter' not in self._oConfig[sType]['defaults']:
                self._oConfig[sType]['defaults']['filter'] = \
                    DEF_PROFILE_FILTER

    def validation_errors(self, oValidationResults):
        """Return a list of string describing any validation errors.

           Returns an empty list if no validation errors occurred. Validation
           results must have been returned by a call to validate() on the same
           config object.
           """
        aErrors = []
        # oValidationResults could be a dict or 'True', so we need to
        # be explicit in this test
        if oValidationResults is True:
            return aErrors

        for (aSections, sKey, _oIgnore) in flatten_errors(self._oConfig,
                                                          oValidationResults):
            if sKey is not None:
                aErrors.append('Key %r in section %r failed validation.' %
                               (sKey, aSections))
            else:
                aErrors.append('Section %r was missing.' % (aSections,))

        return aErrors

    def get_validator(self):
        """Return the validator used to check the configuration."""
        return self._oValidator

    def sanitize(self):
        """Called after validation to clean up a valid config.
           """
        # Subclasses should override this to provide a default setup
        raise NotImplementedError

    def check_writeable(self):
        """Test that we can open the file for writing"""
        self._bWriteable = True
        try:
            oFile = open(self._sFileName, 'a')
            oFile.close()
        except IOError:
            self._bWriteable = False
        return self._bWriteable

    def write(self):
        """Write the config file to disk."""
        if self._bWriteable:
            self._oConfig.write()

    #
    # Open Frame Handling
    #

    def clear_open_frames(self):
        """Clear out old save panes (used before adding new ones)."""
        self._oConfig['open_frames'].clear()

    def open_frames(self):
        """Get the all the panes saved in the config file, and their
           positions."""
        aRes = []
        for sKey, dPane in self._oConfig['open_frames'].items():
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
        dOldProfiles = self._oConfig['per_deck']['frame_profiles'].copy()
        # Clear old state, ensuring we set any botched loads to the
        # default profile
        for sId in dOldProfiles:
            self.set_profile(FRAME, sId, None)
        for sOldId, sNewId in dPaneMap.items():
            if sOldId in dOldProfiles:
                # use set_profile to ensure we call the message bus
                self.set_profile(FRAME, sNewId, dOldProfiles[sOldId])

    # pylint: disable=too-many-arguments
    # We need all the info in the arguments here
    def add_frame(self, iFrameNumber, sType, sName, bVertical, bClosed, iPos,
                  sPaneId):
        """Add a frame with the given position info to the config file"""
        oPanes = self._oConfig['open_frames']
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

    # pylint: enable=too-many-arguments

    #
    # Plugin Config Section Handling
    #

    def get_plugin_key(self, sPlugin, sKey):
        """Get an option from the plugins section.

           Return None if no option is set
           """
        try:
            sResult = self._oConfig['plugins_main'][sPlugin][sKey]
        except KeyError:
            sResult = None
        return sResult

    def set_plugin_key(self, sPlugin, sKey, sValue, bCreateSection=False):
        """Set a value in the plugin section"""
        if bCreateSection and sPlugin not in self._oConfig['plugins_main']:
            self._oConfig['plugins_main'][sPlugin] = {}
        self._oConfig['plugins_main'][sPlugin][sKey] = sValue

    #
    # Filters section
    #

    def get_filters(self):
        """Get all the filters in the config file.

           Filters are return as a list of (sQuery, dVars) tuples.
           """
        return [(oF['query'], oF['vars']) for oF in
                self._oConfig['filters'].values()]

    def get_default_filters(self):
        """Return the default filter list."""
        # Subclasses should override DEFAULT_FILTERS as required
        return self.DEFAULT_FILTERS

    def get_filter_keys(self):
        """Return all the keys for all the filters in the config file."""
        return [(sKey, dFilter['query']) for sKey, dFilter in
                self._oConfig['filters'].items()]

    def get_profiles_for_filter(self, sMatchFilter):
        """Return a dictionary of profiles currently using the given filter"""
        dProfileFilters = {}
        for sType in [CARDSET, FULL_CARDLIST]:
            dProfileFilters[sType] = []
            if sType == CARDSET:
                dConfig = self._oConfig['per_deck']
            else:
                dConfig = self._oConfig[sType]
            sFilter = dConfig['defaults'].get('filter', DEF_PROFILE_FILTER)
            if sFilter == sMatchFilter:
                dProfileFilters[sType].append('defaults')
            for sProfile in dConfig['profiles']:
                sFilter = dConfig['profiles'][sProfile].get('filter',
                                                            DEF_PROFILE_FILTER)
                if sFilter == sMatchFilter:
                    dProfileFilters[sType].append(sProfile)
        return dProfileFilters

    def get_filter(self, sKey):
        """Return the filter associated with the given key.

           Return None if the filter is not known.
           """
        sKey = sKey.lower()
        if sKey in self._oConfig['filters']:
            return self._oConfig['filters'][sKey]['query']
        return None

    def get_filter_values(self, sKey):
        """Return the filter values associated with the given key.

        Return None if the filter is not knonw.
        """
        sKey = sKey.lower()
        if sKey in self._oConfig['filters']:
            return self._oConfig['filters'][sKey]['vars'].dict()
        return None

    # pylint: disable=dangerous-default-value
    # {} is the default here, since we don't change it in the function
    # and a dictionary is what the config file expects a dictionary.
    def add_filter(self, sKey, sQuery, dVars={}):
        """Add a filter to the config file."""
        sKey = sKey.lower()
        if sKey not in self._oConfig['filters']:
            dFilter = {
                'query': sQuery,
                'vars': dVars,
            }
            self._oConfig['filters'][sKey] = dFilter
            MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'add_filter', sKey, sQuery)

    # pylint: enable=dangerous-default-value

    def remove_filter(self, sKey, sFilter):
        """Remove a filter from the file"""
        # Make sure Filer and key match
        sKey = sKey.lower()
        if sKey in self._oConfig['filters'] and \
                sFilter == self._oConfig['filters'][sKey]['query']:
            del self._oConfig['filters'][sKey]
            MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'remove_filter', sKey, sFilter)
            # Cleanup filter from config profiles
            dProfileFilters = self.get_profiles_for_filter(sKey)
            for sType in dProfileFilters:
                aProfiles = dProfileFilters[sType]
                for sProfile in aProfiles:
                    # We set removed filters to the default value
                    # Since we don't allow a name clash, this will
                    # always return None as the filter text, which
                    # is the desired behaviour
                    if sProfile == 'defaults':
                        self.set_profile_option(sType, None, 'filter',
                                                DEF_PROFILE_FILTER)
                    else:
                        self.set_profile_option(sType, sProfile, 'filter',
                                                DEF_PROFILE_FILTER)

    def replace_filter(self, sKey, sOldFilter, sNewFilter):
        """Replace a filter in the file with new filter"""
        sKey = sKey.lower()
        if sKey in self._oConfig['filters'] and \
                sOldFilter == self._oConfig['filters'][sKey]['query']:
            self._oConfig['filters'][sKey]['query'] = sNewFilter
            MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'replace_filter', sKey,
                               sOldFilter, sNewFilter)

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
                return self._dLocalFrameOptions[sFrame][sKey]
        except KeyError:
            pass

        dPerDeck = self._oConfig['per_deck']

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
                return self._oConfig['per_deck']['defaults'][sKey]
            return self._oConfig['per_deck']['profiles'][sProfile][sKey]
        except KeyError:
            return None

    def get_local_frame_option(self, sFrame, sKey):
        """Get the value of a per-deck option for a local frame."""
        try:
            return self._dLocalFrameOptions[sFrame][sKey]
        except KeyError:
            return None

    def set_profile_option(self, sType, sProfile, sKey, sValue):
        """Set the value of a option for a profile for sType.

           If sValue is None, remove the key. New profiles are
           created as needed.
           """
        if sType == CARDSET:
            dConfig = self._oConfig['per_deck']
        else:
            dConfig = self._oConfig[sType]
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
            MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'profile_option_changed',
                               sType, sProfile, sKey)

    def set_local_frame_option(self, sFrame, sKey, sValue):
        """Set the value of an option in the local frame option dictionary.

        If sValue is None, remove the key.
        """
        if sFrame in self._dLocalFrameOptions:
            dOptions = self._dLocalFrameOptions[sFrame]
        else:
            dOptions = {}
            self._dLocalFrameOptions[sFrame] = dOptions

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
            MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'profile_changed', FRAME, sFrame)

    def clear_frame_profile(self, sId):
        """Clear any pane profiles set for this frame"""
        dProfiles = self._oConfig['per_deck']['frame_profiles']
        if sId in dProfiles:
            # We should only be called while the pane is being closed,
            # so we don't send a message on the MessageBus to avoid a
            # pointless reload.
            del dProfiles[sId]

    def clear_cardset_profile(self, sId):
        """Clear any profiles set for this cardset"""
        # We don't need to worry about the pane profiles, as the
        # the frames will be explicitly closed, which will take care of those
        # for us.
        dProfiles = self._oConfig['per_deck']['cardset_profiles']
        if sId in dProfiles:
            # We should only be called while the pane is being closed,
            # so we don't send a message on the MessageBus to avoid a
            # pointless reload.
            del dProfiles[sId]

    def fix_profile_mapping(self, dOldMap, dNewMap):
        """Update the card set profiles to a new id -> name mapping"""
        # We need to reverse of dNewMapping. Since both name and id are
        # unique, this is safe
        dNewRev = dict(zip(dNewMap.values(), dNewMap.keys()))
        dOldProfiles = self._oConfig['per_deck']['cardset_profiles'].copy()
        dProfiles = self._oConfig['per_deck']['cardset_profiles']
        dProfiles.clear()
        for sId, sProfile in dOldProfiles.items():
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
        if sType in (CARDSET, FRAME):
            if sType == CARDSET:
                dProfiles = self._oConfig['per_deck']['cardset_profiles']
            else:
                dProfiles = self._oConfig['per_deck']['frame_profiles']
            if dProfiles.get(sId) == sProfile:
                return
            if sProfile is None:
                del dProfiles[sId]
            else:
                dProfiles[sId] = sProfile
        elif (sType == FULL_CARDLIST and sId == FULL_CARDLIST) or \
                (sType == CARDSET_LIST and sId == CARDSET_LIST):
            sCurProfile = self._oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                return
            if sProfile is None:
                del self._oConfig[sType]['current profile']
            else:
                self._oConfig[sType]['current profile'] = sProfile
        else:
            # Unrecognised type / cardset combo
            return
        MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'profile_changed', sType, sId)

    def get_profile(self, sType, sId):
        """Return the current profile of the cardset/cardlist/cardset list."""
        if sType == CARDSET:
            return self._oConfig['per_deck']['cardset_profiles'].get(sId)
        if sType == FRAME:
            return self._oConfig['per_deck']['frame_profiles'].get(sId)
        if (sType == FULL_CARDLIST and sId == FULL_CARDLIST) or \
                (sType == CARDSET_LIST and sId == CARDSET_LIST):
            return self._oConfig[sType].get('current profile')
        return None

    def clear_profiles(self, sType, sProfile):
        """Find all cardsets/frames using this profile, and change them to
          the default"""
        if sType in (CARDSET, FRAME):
            if sType == CARDSET:
                dProfiles = self._oConfig['per_deck']['cardset_profiles']
            else:
                dProfiles = self._oConfig['per_deck']['frame_profiles']
            # Loop over a copy, as we may change the dict
            for sId, sCurProfile in dProfiles.items():
                if sCurProfile == sProfile:
                    self.set_profile(sType, sId, None)
        else:
            sCurProfile = self._oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                self.set_profile(sType, sType, None)

    def remove_profile(self, sType, sProfile):
        """Remove a profile from the file"""
        dData = {}
        if sType in (CARDSET, FRAME):
            dData = self._oConfig['per_deck']['profiles']
        elif sType == CARDSET_LIST:
            dData = self._oConfig['cardset list']['profiles']
        elif sType == FULL_CARDLIST:
            dData = self._oConfig['cardlist']['profiles']
        if sProfile in dData:
            if sType in (CARDSET, FRAME):
                # Need to clear both lists in this case
                self.clear_profiles(FRAME, sProfile)
                self.clear_profiles(CARDSET, sProfile)
            else:
                self.clear_profiles(sType, sProfile)
            del dData[sProfile]
            MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'remove_profile', sType, sProfile)

    def frame_profiles(self):
        """Return a dictionary of frame id -> profile mappings."""
        return dict(self._oConfig['per_deck']['frame_profiles'])

    def get_profile_users(self, sType, sProfile):
        """Returns a list of all card sets or panes that use the
           given profile"""
        if sType == CARDSET_LIST:
            sCurProfile = self._oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                return ['Card Set List']
        elif sType == FULL_CARDLIST:
            sCurProfile = self._oConfig[sType].get('current profile')
            if sCurProfile == sProfile:
                return ['Full Card List']
        elif sType == CARDSET:
            aUsers = []
            for dProfiles in (self._oConfig['per_deck']['cardset_profiles'],
                              self._oConfig['per_deck']['frame_profiles'],
                             ):
                for sId, sCurProfile in dProfiles.items():
                    if sProfile == sCurProfile:
                        aUsers.append(sId)
            return aUsers
        return None

    def profiles(self, sType):
        """Return a list of profile keys."""
        if sType in (CARDSET, FRAME):
            return list(self._oConfig['per_deck']['profiles'].keys())
        if sType == CARDSET_LIST:
            return list(self._oConfig['cardset list']['profiles'].keys())
        if sType == FULL_CARDLIST:
            return list(self._oConfig['cardlist']['profiles'].keys())
        # Unkown type
        return None

    def profile_options(self, sType):
        """Return a list of per-deck option names."""
        if sType in (CARDSET, FRAME):
            return self._oConfig['per_deck']['defaults'].keys()
        return self._oConfig[sType]['defaults'].keys()

    def get_option_spec(self, sType, sKey):
        """Return the config spec for a given option."""
        if sType in (CARDSET, FRAME):
            return self._oConfigSpec['per_deck']['defaults'][sKey]
        return self._oConfigSpec[sType]['defaults'][sKey]

    def get_profile_option(self, sType, sProfile, sKey):
        """Get the value of a per-deck option for a profile."""
        if sType in (CARDSET, FRAME):
            return self.get_deck_profile_option(sProfile, sKey)
        try:
            if sProfile is None or sProfile.lower() == "default":
                return self._oConfig[sType]['defaults'][sKey]
            # We fall back to the defaults if the key isn't set yet
            try:
                return self._oConfig[sType]['profiles'][sProfile][sKey]
            except KeyError:
                return self._oConfig[sType]['defaults'][sKey]
        except KeyError:
            return None

    #
    # Application Level Config Settings
    #

    def get_save_on_exit(self):
        """Query the 'save on exit' option."""
        return self._oConfig['main']['save on exit']

    def set_save_on_exit(self, bSaveOnExit):
        """Set the 'save on exit' option."""
        self._oConfig['main']['save on exit'] = bSaveOnExit

    def get_check_for_updates(self):
        """Query the 'check for updates on startup' option."""
        return self._oConfig['main']['check for updates on startup']

    def set_check_for_updates(self, bCheck):
        """Query the 'check for updates on startup' option."""
        self._oConfig['main']['check for updates on startup'] = bCheck

    def get_save_precise_pos(self):
        """Query the 'save pane sizes' option."""
        return self._oConfig['main']['save pane sizes']

    def set_save_precise_pos(self, bSavePos):
        """Set the 'save pane sizes' option."""
        self._oConfig['main']['save pane sizes'] = bSavePos

    def get_save_window_size(self):
        """Query the 'save window size' option."""
        return self._oConfig['main']['save window size']

    def set_save_window_size(self, bSavePos):
        """Set the 'save window size' option."""
        self._oConfig['main']['save window size'] = bSavePos

    def set_database_uri(self, sDatabaseURI):
        """Set the configured database URI"""
        self._oConfig['main']['database url'] = sDatabaseURI

    def get_database_uri(self):
        """Get database URI from the config file"""
        return self._oConfig['main']['database url']

    def get_icon_path(self):
        """Get the icon path from the config file"""
        return self._oConfig['main']['icon path']

    def set_icon_path(self, sPath):
        """Set the configured icon path"""
        self._oConfig['main']['icon path'] = sPath

    def get_window_size(self):
        """Get the saved window size from the config file."""
        iWidth, iHeight = self._oConfig['main']['window size']
        return iWidth, iHeight

    def set_window_size(self, tSize):
        """Save the current window size."""
        self._oConfig['main']['window size'] = tSize

    def get_postfix_the_display(self):
        """Get the 'postfix name display' option."""
        return self._oConfig['main']['postfix name display']

    def set_postfix_the_display(self, bPostfix):
        """Set the 'postfix name display' option."""
        self._oConfig['main']['postfix name display'] = bPostfix
        MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'set_postfix_the_display', bPostfix)

    def get_socket_timeout(self):
        """Get the timeout config value"""
        return self._oConfig['main']['socket timeout']
