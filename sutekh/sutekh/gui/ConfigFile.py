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

    def profile_changed(self, sProfile, sKey):
        """One of the per-deck configuration items changed."""
        pass

    def frame_profile_changed(self, sFrame, sNewProfile):
        """The profile associated with a frame changed."""
        pass

    def cardset_profile_changed(self, sCardset, sNewProfile):
        """The profile associated with a cardset changed."""
        pass

    def cardlist_profile_changed(self, sProfile, sKey):
        """One of the WW cardlist configuration items changed."""
        pass

    def cardlist_frame_profile_changed(self, sNewProfile):
        """The profile associated with the WW cardlist frame changed."""
        pass

    def cardset_list_profile_changed(self, sProfile, sKey):
        """One of the cardset list configuration items changed."""
        pass

    def cardset_list_frame_profile_changed(self, sNewProfile):
        """The profile associated with the cardset list frame changed."""
        pass


class ConfigFile(object):
    """Handle the setup and management of the config file.

       Ensure that the needed sections exist, and that sensible
       defaults values are assigned.

       Filters are saved to the config file, and interested objects
       can register as listeners on the config file to respond to
       changes to the filters.
       """
    # pylint: disable-msg=R0904
    # We need to provide fine-grained access to all the data,
    # so lots of methods

    dCustomConfigTypes = {
        'option_list': is_option_list,
    }

    def __init__(self, sFileName):
        self.__sFileName = sFileName
        self.__oConfigSpec = None
        self.__oConfig = None
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
                    False, -1)
            self.add_frame(2, 'Card Text', 'Card Text', False, False, -1)
            self.add_frame(3, 'Card Set List', 'Card Set List', False, False,
                    -1)
            self.add_frame(4, 'physical_card_set', 'My Collection', False,
                    False, -1)

    def write(self):
        """Write the config file to disk."""
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
        # TODO: return old pane id so it can be restored so that
        #       pane id -> profile mappings still make sense
        # TODO: Update pane id used by profile to be identical to
        #       open frame pane keys 
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
                dPane['orientation'] == 'V',
                dPane['orientation'] == 'C',
                iPos,
            ))

        aRes.sort() # Numbers denote ordering
        return aRes

    # pylint: disable-msg=R0913
    # We need all the info in the arguments here
    def add_frame(self, iFrameNumber, sType, sName, bVertical, bClosed, iPos):
        """Add a frame with the given position info to the config file"""
        oPanes = self.__oConfig['open_frames']
        sKey = 'pane %d' % iFrameNumber

        oPanes[sKey] = {}
        oNewPane = oPanes[sKey]

        oNewPane['type'] = sType
        oNewPane['name'] = sName

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

    def set_plugin_key(self, sPlugin, sKey, sValue):
        """Set a value in the plugin section"""
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

    def add_filter(self, sKey, sQuery, dVars={}):
        """Add a filter to the config file."""
        sKey = sKey.lower()
        if sKey not in self.__oConfig['filters']:
            dFilter = {
                'query': sQuery,
                'vars': dVars
            }
            self.__oConfig['filters'][sKey] = dFilter
            for oListener in self.listeners():
                oListener.add_filter(sKey, sQuery)

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

    def get_deck_option(self, sFrame, sCardset, sKey):
        """Retrieve the value of a per-deck option.

           Either sFrame or sCardset may be None, in
           which case the frame or cardset option look-up
           is skipped.
           """
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

    def set_deck_profile_option(self, sProfile, sKey, sValue):
        """Set the value of a per-deck option for a profile.

           If sValue is None, remove the key. New profiles are
           created as needed.
           """
        if sProfile is None:
            dProfile = self.__oConfig['per_deck']['defaults']
        elif sProfile in self.__oConfig['per_deck']['profiles']:
            dProfile = self.__oConfig['per_deck']['profiles'][sProfile]
        else:
            # configobj replaces the dict with a config object, so
            # trigger the creation of the config object, then set
            # dProfile to it
            self.__oConfig['per_deck']['profiles'][sProfile] = {}
            dProfile = self.__oConfig['per_deck']['profiles'][sProfile]

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
                oListener.profile_changed(sProfile, sKey)

    def set_frame_profile(self, sFrame, sProfile):
        """Set the profile associated with a frame id."""
        dFrameProfiles = self.__oConfig['per_deck']['frame_profiles']
        if dFrameProfiles.get(sFrame) == sProfile:
            return
        if sProfile is None:
            del dFrameProfiles[sFrame]
        else:
            dFrameProfiles[sFrame] = sProfile
        for oListener in self.listeners():
            oListener.frame_profile_changed(sFrame, sProfile)

    def set_cardset_profile(self, sCardset, sProfile):
        """Set the profile associated with a cardset id."""
        dCardsetProfiles = self.__oConfig['per_deck']['cardset_profiles']
        if dCardsetProfiles.get(sCardset) == sProfile:
            return
        if sProfile is None:
            del dCardsetProfiles[sCardset]
        else:
            dCardsetProfiles[sCardset] = sProfile
        for oListener in self.listeners():
            oListener.cardset_profile_changed(sCardset, sProfile)

    def get_frame_profile(self, sFrame):
        """Return the current profile of the frame."""
        return self.__oConfig['per_deck']['frame_profiles'].get(sFrame)

    def get_cardset_profile(self, sCardset):
        """Return the current profile of the cardset."""
        return self.__oConfig['per_deck']['cardset_profiles'].get(sCardset)

    def get_cardlist_profile(self):
        """Return the current profile of the cardset."""
        return self.__oConfig['cardlist'].get('current profile')

    def set_cardlist_profile(self, sProfile):
        """Set the profile associated with the WW cardlist."""
        sCurProfile = self.__oConfig['cardlist'].get('current profile')
        if sCurProfile == sProfile:
            return
        if sProfile:
            self.__oConfig['cardlist']['current profile'] = sProfile
        else:
            del self.__oConfig['cardlist']['current profile']

        for oListener in self.listeners():
            oListener.cardlist_frame_profile_changed(sProfile)

    def get_cardset_list_profile(self):
        """Return the current profile of the cardset."""
        return self.__oConfig['cardset list'].get('current profile')

    def set_cardset_list_profile(self, sProfile):
        """Set the profile associated with the WW cardlist."""
        sCurProfile = self.__oConfig['cardset list'].get('current profile')
        if sCurProfile == sProfile:
            return
        if sProfile:
            self.__oConfig['cardset list']['current profile'] = sProfile
        else:
            del self.__oConfig['cardset list']['current profile']

        for oListener in self.listeners():
            oListener.cardset_list_frame_profile_changed(sProfile)


    def frame_profiles(self):
        """Return a dictionary of frame id -> profile mappings."""
        return dict(self.__oConfig['per_deck']['frame_profiles'])

    def cardset_profiles(self):
        """Return a dictionary of cardset id -> profile mappings."""
        return dict(self.__oConfig['per_deck']['cardset_profiles'])

    def profiles(self):
        """Return a list of profile keys."""
        return list(self.__oConfig['per_deck']['profiles'].keys())

    def deck_options(self):
        """Return a list of per-deck option names."""
        return self.__oConfig['per_deck']['defaults'].keys()

    def get_deck_option_spec(self, sKey):
        """Return the config spec for a given option."""
        return self.__oConfigSpec['per_deck']['defaults'][sKey]

    def cardlist_options(self):
        """Return a list of WW cardlist option names."""
        return self.__oConfig['cardlist']['defaults'].keys()

    def get_cardlist_option_spec(self, sKey):
        """Return the config spec for a given option."""
        return self.__oConfigSpec['cardlist']['defaults'][sKey]

    def cardlist_profiles(self):
        """Return a list of profile keys."""
        return list(self.__oConfig['cardlist']['profiles'].keys())

    def cardset_list_options(self):
        """Return a list of cardset list option names."""
        return self.__oConfig['cardset list']['defaults'].keys()

    def get_cardset_list_option_spec(self, sKey):
        """Return the config spec for a given option."""
        return self.__oConfigSpec['cardset list']['defaults'][sKey]

    def cardset_list_profiles(self):
        """Return a list of profile keys."""
        return list(self.__oConfig['cardset list']['profiles'].keys())

    def get_current_cardlist_profile(self):
        """Get the current WW cardlist profile"""
        return self.__oConfig['cardlist'].get('current profile')

    def get_current_cardset_list_profile(self):
        """Get the current cardset list profile"""
        return self.__oConfig['cardset list'].get('current profile')

    def get_cardlist_profile_option(self, sProfile, sKey):
        """Get the value of a per-deck option for a profile."""
        try:
            if sProfile is None or sProfile.lower() == "default":
                return self.__oConfig['cardlist']['defaults'][sKey]
            else:
                return self.__oConfig['cardlist']['profiles'][sProfile][sKey]
        except KeyError:
            return None

    def set_cardlist_profile_option(self, sProfile, sKey, sValue):
        """Set the value of a per-deck option for a profile.

           If sValue is None, remove the key. New profiles are
           created as needed.
           """
        if sProfile is None:
            dProfile = self.__oConfig['cardlist']['defaults']
        elif sProfile in self.__oConfig['cardlist']['profiles']:
            dProfile = self.__oConfig['cardlist']['profiles'][sProfile]
        else:
            # configobj replaces the dict with a config object, so
            # trigger the creation of the config object, then set
            # dProfile to it
            self.__oConfig['cardlist']['profiles'][sProfile] = {}
            dProfile = self.__oConfig['cardlist']['profiles'][sProfile]

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
                oListener.cardlist_profile_changed(sProfile, sKey)


    def get_cardset_list_profile_option(self, sProfile, sKey):
        """Get the value of a per-deck option for a profile."""
        try:
            if sProfile is None or sProfile.lower() == "default":
                return self.__oConfig['cardset list']['defaults'][sKey]
            else:
                return self.__oConfig['cardset list']['profiles'][sProfile][sKey]
        except KeyError:
            return None

    def set_cardset_list_profile_option(self, sProfile, sKey, sValue):
        """Set the value of a per-deck option for a profile.

           If sValue is None, remove the key. New profiles are
           created as needed.
           """
        if sProfile is None:
            dProfile = self.__oConfig['cardset list']['defaults']
        elif sProfile in self.__oConfig['cardset list']['profiles']:
            dProfile = self.__oConfig['cardset list']['profiles'][sProfile]
        else:
            # configobj replaces the dict with a config object, so
            # trigger the creation of the config object, then set
            # dProfile to it
            self.__oConfig['cardset list']['profiles'][sProfile] = {}
            dProfile = self.__oConfig['cardset list']['profiles'][sProfile]

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
                oListener.cardset_list_profile_changed(sProfile, sKey)

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

    # TODO: add loader for old config files
