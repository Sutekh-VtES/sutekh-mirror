# HTMLTextView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# TextView Object that displays an HTML file
# Copyright 2005, 2006, 2007 Gustavo J. A. M. Carneiro
# Changes for Sutekh, Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details
# Original version downloaded from http://www.gnome.org/~gjc/htmltextview.py
# April 2008

'''
A gtk.TextView-based renderer for XHTML-IM, as described in:
  http://www.jabber.org/jeps/jep-0071.html
'''

import gobject
import pango
import gtk
import re
import warnings
import operator
import xml.sax, xml.sax.handler
from cStringIO import StringIO
# pylint: disable-msg=E0611
# pylint doesn't see resource_stream here, for some reason
from pkg_resources import resource_stream, resource_exists
# pylint: enable-msg=E0611
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

oWhiteSpaceRegex = re.compile("\\s+")
oAllWhiteSpaceRegex = re.compile("^\\s*$")

## pixels = points * fResolution
fResolution = 0.3514598*(gtk.gdk.screen_height() /
                    float(gtk.gdk.screen_height_mm()))

def _parse_css_color(sColor):
    '''_parse_css_color(css_color) -> gtk.gdk.Color'''
    if sColor.startswith("rgb(") and sColor.endswith(')'):
        iRed, iGreen, iBlue = [int(c)*257 for c in sColor[4:-1].split(',')]
        return gtk.gdk.Color(iRed, iGreen, iBlue)
    else:
        return gtk.gdk.color_parse(sColor)

class HtmlHandler(xml.sax.handler.ContentHandler):
    # pylint: disable-msg=R0201
    # can't break these into functions
    """Parse the HTML imput and update the gtk.TextView"""
    def __init__(self, oTextView, oStartIter):
        xml.sax.handler.ContentHandler.__init__(self)
        self._oTextBuf = oTextView.get_buffer()
        self._oTextView = oTextView
        self._oIter = oStartIter
        self._sText = ''
        self._aStyles = [] # a gtk.TextTag or None, for each span level
        self._aListCounters = [] # stack (top at head) of list
                                # counters, or None for unordered list
        self._bInTitle = False

    def _parse_style_color(self, oTag, sValue):
        """Convert style value to TextView foreground color"""
        oColor = _parse_css_color(sValue)
        oTag.set_property("foreground-gdk", oColor)

    def _parse_style_background_color(self, oTag, sValue):
        """Convert background value to TextView background color."""
        oColor = _parse_css_color(sValue)
        oTag.set_property("background-gdk", oColor)
        if gtk.gtk_version >= (2, 8):
            oTag.set_property("paragraph-background-gdk", oColor)


    if gtk.gtk_version >= (2, 8, 5) or gobject.pygtk_version >= (2, 8, 1):

        def _get_current_attributes(self):
            """Get current attributes."""
            aAttrs = self._oTextView.get_default_attributes()
            self._oIter.backward_char()
            self._oIter.get_attributes(aAttrs)
            self._oIter.forward_char()
            return aAttrs

    else:

        ## Workaround http://bugzilla.gnome.org/show_bug.cgi?id=317455
        def _get_current_style_attr(self, sPropName, fCombOper=None):
            """Get the current style attributes."""
            aTags = [oTag for oTag in self._aStyles if oTag is not None]
            aTags.reverse()
            sIsSetName = sPropName + "-set"
            oValue = None
            for oTag in aTags:
                if oTag.get_property(sIsSetName):
                    if oValue is None:
                        oValue = oTag.get_property(sPropName)
                        if fCombOper is None:
                            return oValue
                    else:
                        oValue = fCombOper(oValue,
                                oTag.get_property(sPropName))
            return oValue

        class _FakeAttrs(object):
            """Fake class with default attributes"""
            __slots__ = ("font", "font_scale")
            # pylint: disable-msg=C0103
            # names need to match gtk's convention
            def __init__(self):
                self.font_scale = None
                self.font = None

        def _get_current_attributes(self):
            """Get current attributes."""
            # pylint: disable-msg=C0103
            # font, font-scale required by design
            aAttrs = self._FakeAttrs()
            aAttrs.font_scale = self._get_current_style_attr("scale",
                                                            operator.mul)
            if aAttrs.font_scale is None:
                aAttrs.font_scale = 1.0
            aAttrs.font = self._get_current_style_attr("font-desc")
            if aAttrs.font is None:
                aAttrs.font = self._oTextView.style.font_desc
            return aAttrs

    def _parse_length(self, sValue, bFontRelative, fCallback, *aArgs):
        """Parse/calc length, converting to pixels.

           calls callback(length, *aArgs) when the length is first computed
           or changes
           """
        # pylint: disable-msg=W0142
        # *magic required here
        if sValue.endswith('%'):
            fFrac = float(sValue[:-1])/100
            if bFontRelative:
                oAttrs = self._get_current_attributes()
                fFontSize = oAttrs.font.get_size() / pango.SCALE
                fCallback(fFrac * fResolution * fFontSize, *aArgs)
            else:
                ## CSS says "Percentage values: refer to width of the closest
                ##           block-level ancestor"
                ## This is difficult/impossible to implement, so we use
                ## textview width instead; a reasonable approximation..
                oAlloc = self._oTextView.get_allocation()
                self.__parse_length_frac_cb(self._oTextView, oAlloc,
                        fFrac, fCallback, aArgs)
                self._oTextView.connect("size-allocate",
                        self.__parse_length_frac_cb, fFrac,
                        fCallback, aArgs)

        elif sValue.endswith('pt'): # points
            fCallback(float(sValue[:-2]) * fResolution, *aArgs)
        elif sValue.endswith('em'): # ems, the height of the element's font
            oAttrs = self._get_current_attributes()
            fFontSize = oAttrs.font.get_size() / pango.SCALE
            fCallback(float(sValue[:-2]) * fResolution * fFontSize, *aArgs)
        elif sValue.endswith('ex'): # x-height, ~ the height of the letter 'x'
            ## FIXME: figure out how to calculate this correctly
            ##        for now 'em' size is used as approximation
            oAttrs = self._get_current_attributes()
            fFontSize = oAttrs.font.get_size() / pango.SCALE
            fCallback(float(sValue[:-2]) * fResolution * fFontSize, *aArgs)
        elif sValue.endswith('px'): # pixels
            fCallback(int(sValue[:-2]), *aArgs)
        else:
            warnings.warn("Unable to parse length value '%s'" % sValue)

    @staticmethod
    def __parse_font_size_cb(fLength, oTag):
        """Callback for font size calculations."""
        oTag.set_property("size-points", fLength/fResolution)

    def _parse_style_font_size(self, oTag, sValue):
        """Parse the font size attribute"""
        try:
            iScale = {
                "xx-small": pango.SCALE_XX_SMALL,
                "x-small": pango.SCALE_X_SMALL,
                "small": pango.SCALE_SMALL,
                "medium": pango.SCALE_MEDIUM,
                "large": pango.SCALE_LARGE,
                "x-large": pango.SCALE_X_LARGE,
                "xx-large": pango.SCALE_XX_LARGE,
                } [sValue]
        except KeyError:
            pass
        else:
            oAttrs = self._get_current_attributes()
            oTag.set_property("scale", iScale / oAttrs.font_scale)
            return
        if sValue == 'smaller':
            oTag.set_property("scale", pango.SCALE_SMALL)
            return
        if sValue == 'larger':
            oTag.set_property("scale", pango.SCALE_LARGE)
            return
        self._parse_length(sValue, True, self.__parse_font_size_cb, oTag)

    def _parse_style_font_style(self, oTag, sValue):
        """Parse the font style attribute"""
        try:
            iStyle = {
                "normal": pango.STYLE_NORMAL,
                "italic": pango.STYLE_ITALIC,
                "oblique": pango.STYLE_OBLIQUE,
                } [sValue]
        except KeyError:
            warnings.warn("unknown font-style %s" % sValue)
        else:
            oTag.set_property("style", iStyle)

    @staticmethod
    def __frac_length_tag_cb(fLength, oTag, sPropName):
        """Callback used by _parse_length for handling the margin style
           settings."""
        oTag.set_property(sPropName, fLength)

    def _parse_style_margin_left(self, oTag, sValue):
        """Handle the margin left style attribute."""
        self._parse_length(sValue, False, self.__frac_length_tag_cb, oTag,
                "left-margin")

    def _parse_style_margin_right(self, oTag, sValue):
        """Hanlde the margin right style attribute."""
        self._parse_length(sValue, False, self.__frac_length_tag_cb, oTag,
                "right-margin")

    def _parse_style_font_weight(self, oTag, sValue):
        """Adjust the font to match the font weight specification."""
        ## missing 'bolder' and 'lighter', but that's not important for us
        try:
            iWeight = {
                '100': pango.WEIGHT_ULTRALIGHT,
                '200': pango.WEIGHT_ULTRALIGHT,
                '300': pango.WEIGHT_LIGHT,
                '400': pango.WEIGHT_NORMAL,
                '500': pango.WEIGHT_NORMAL,
                '600': pango.WEIGHT_BOLD,
                '700': pango.WEIGHT_BOLD,
                '800': pango.WEIGHT_ULTRABOLD,
                '900': pango.WEIGHT_HEAVY,
                'normal': pango.WEIGHT_NORMAL,
                'bold': pango.WEIGHT_BOLD,
                } [sValue]
        except KeyError:
            warnings.warn("unknown font-style %s" % sValue)
        else:
            oTag.set_property("weight", iWeight)

    def _parse_style_font_family(self, oTag, sValue):
        """Change the font family."""
        oTag.set_property("family", sValue)

    def _parse_style_text_align(self, oTag, sValue):
        """Set the text alignment style."""
        try:
            iAlign = {
                'left': gtk.JUSTIFY_LEFT,
                'right': gtk.JUSTIFY_RIGHT,
                'center': gtk.JUSTIFY_CENTER,
                'justify': gtk.JUSTIFY_FILL,
                } [sValue]
        except KeyError:
            warnings.warn("Invalid text-align:%s requested" % sValue)
        else:
            oTag.set_property("justification", iAlign)

    def _parse_style_text_decoration(self, oTag, sValue):
        """Set the pango properties for the tag to match the desired html text
           decoration."""
        if sValue == "none":
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", False)
        elif sValue == "underline":
            oTag.set_property("underline", pango.UNDERLINE_SINGLE)
            oTag.set_property("strikethrough", False)
        elif sValue == "overline":
            warnings.warn("text-decoration:overline not implemented")
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", False)
        elif sValue == "line-through":
            oTag.set_property("underline", pango.UNDERLINE_NONE)
            oTag.set_property("strikethrough", True)
        elif sValue == "blink":
            warnings.warn("text-decoration:blink not implemented")
        else:
            warnings.warn("text-decoration:%s not implemented" % sValue)


    ## build a dictionary mapping styles to methods, for greater speed
    __style_methods = dict()
    for sStyle in ["background-color", "color", "font-family", "font-size",
                  "font-style", "font-weight", "margin-left", "margin-right",
                  "text-align", "text-decoration"]:
        try:
            fMethod = locals()["_parse_style_%s" % sStyle.replace('-', '_')]
        except KeyError:
            warnings.warn("Style attribute '%s' not yet implemented" % sStyle)
        else:
            __style_methods[sStyle] = fMethod

    def _get_style_tags(self):
        """Get the current set of style tags"""
        return [oTag for oTag in self._aStyles if oTag is not None]

    def _begin_span(self, sStyle, oTag=None):
        """Start a <span> section"""
        if sStyle is None:
            self._aStyles.append(oTag)
            return None
        if oTag is None:
            oTag = self._oTextBuf.create_tag()
        for sAttr, sVal in [item.split(':', 1) for item in sStyle.split(';')]:
            sAttr = sAttr.strip().lower()
            sVal = sVal.strip()
            try:
                fMethod = self.__style_methods[sAttr]
            except KeyError:
                warnings.warn("Style attribute '%s' requested "
                              "but not yet implemented" % sAttr)
            else:
                fMethod(self, oTag, sVal)
        self._aStyles.append(oTag)

    def _end_span(self):
        """End a <span> section"""
        self._aStyles.pop(-1)

    def _insert_text(self, sText):
        """Insert text into the TextBuffer"""
        aTags = self._get_style_tags()
        if aTags:
            # pylint: disable-msg=W0142
            # * magic required
            self._oTextBuf.insert_with_tags(self._oIter, sText, *aTags)
        else:
            self._oTextBuf.insert(self._oIter, sText)

    def _flush_text(self):
        """Flush any pending text."""
        if not self._sText:
            return
        self._insert_text(self._sText.replace('\n', ''))
        self._sText = ''

    # pylint: disable-msg=R0913, W0613
    # Arguments needed by function signature
    def _anchor_event(self, oTag, oTextview, oEvent, oIter, oHref, oType_):
        """Something happened to a link, so see if we need to react."""
        if oEvent.type == gtk.gdk.BUTTON_PRESS and oEvent.button == 1:
            self._oTextView.emit("url-clicked", oHref, oType_)
            return True
        return False

    # Arguments needed so this can be called via 'size-allocate' event
    def __parse_length_frac_cb(self, oTextView, oAllocation,
            fFrac, fCallback, aArgs):
        """call the required callback function when the size allocation
           changes."""
        # pylint: disable-msg=W0142
        # *magic required here
        fCallback(oAllocation.width * fFrac, *aArgs)

    # pylint: enable-msg=R0913, W0613

    def characters(self, sContent):
        """Process the character comments of an element."""
        if oAllWhiteSpaceRegex.match(sContent) is not None:
            return
        if self._bInTitle:
            return
        #if self._sText:
        #    self._sText += ' '
        self._sText += oWhiteSpaceRegex.sub(' ', sContent)

    # pylint: disable-msg=C0103
    # startElement, endElement names are require
    def startElement(self, sName, oAttrs):
        """Parser start element handler"""
        # pylint: disable-msg=R0912, R0915
        # sax content parser, so it is is a massive if..elif.. statement
        self._flush_text()
        try:
            oStyle = oAttrs['style']
        except KeyError:
            oStyle = None

        oTag = None
        if sName == 'a':
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('foreground', '#0000ff')
            oTag.set_property('underline', pango.UNDERLINE_SINGLE)
            try:
                oType_ = oAttrs['type']
            except KeyError:
                oType_ = None
            oTag.connect('event', self._anchor_event, oAttrs['href'], oType_)
            oTag.is_anchor = True
        elif sName in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            oTag = self._oTextBuf.create_tag()
            oTag.set_property('underline', pango.UNDERLINE_SINGLE)
            if sName == 'h1':
                oTag.set_property('weight', pango.WEIGHT_HEAVY)
                oTag.set_property('scale', pango.SCALE_X_LARGE)
            elif sName == 'h2':
                oTag.set_property('weight', pango.WEIGHT_ULTRABOLD)
                oTag.set_property('scale', pango.SCALE_LARGE)
            elif sName == 'h3':
                oTag.set_property('weight', pango.WEIGHT_BOLD)
        elif sName == 'title':
            self._bInTitle = True
            return

        self._begin_span(oStyle, oTag)

        if sName == 'br':
            pass # handled in endElement
        elif sName == 'p':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'div':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'span':
            pass
        elif sName == 'ul':
            if not self._oIter.starts_line():
                self._insert_text("\n")
            self._aListCounters.insert(0, None)
        elif sName == 'ol':
            if not self._oIter.starts_line():
                self._insert_text("\n")
            self._aListCounters.insert(0, 0)
        elif sName == 'li':
            if self._aListCounters[0] is None:
                sListHead = unichr(0x2022)
            else:
                self._aListCounters[0] += 1
                sListHead = "%i." % self._aListCounters[0]
            self._sText = ' '*len(self._aListCounters)*4 + sListHead + ' '
        elif sName == 'img':
            # pylint: disable-msg=W0703
            # we want to catch all errors here
            try:
                # Is this the right way? Not sure of my understanding of the
                # pkg_resources docs.
                oFile = resource_stream('sutekh', '/docs/' + oAttrs['src'])
                oLoader = gtk.gdk.PixbufLoader()
                oLoader.write(oFile.read())
                oLoader.close()
                oPixbuf = oLoader.get_pixbuf()
            except Exception:
                oPixbuf = None
                try:
                    sAlt = oAttrs['alt']
                except KeyError:
                    sAlt = "Broken image"
            if oPixbuf is not None:
                aTags = self._get_style_tags()
                if aTags:
                    oTmpMark = self._oTextBuf.create_mark(None, self._oIter,
                            True)

                self._oTextBuf.insert_pixbuf(self._oIter, oPixbuf)

                if aTags:
                    oStart = self._oTextBuf.get_iter_at_mark(oTmpMark)
                    for oTag in aTags:
                        self._oTextBuf.apply_tag(oTag, oStart, self._oIter)
                    self._oTextBuf.delete_mark(oTmpMark)
            else:
                self._insert_text("[IMG: %s]" % sAlt)
        elif sName == 'body':
            pass
        elif sName == 'a':
            pass
        elif sName == 'head':
            pass
        elif sName == 'html':
            pass
        elif sName in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            pass
        else:
            warnings.warn("Unhandled element '%s'" % sName)

    def endElement(self, sName):
        """Handle the end of a tag"""
        # pylint: disable-msg=R0912, R0915
        # sax content parser, so it is is a massive if..elif.. statement
        if sName == 'title':
            self._bInTitle = False
            return
        self._flush_text()
        if sName == 'p':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'div':
            if not self._oIter.starts_line():
                self._insert_text("\n")
        elif sName == 'span':
            pass
        elif sName == 'body':
            pass
        elif sName == 'br':
            self._insert_text("\n")
        elif sName == 'ul':
            self._aListCounters.pop()
        elif sName == 'ol':
            self._aListCounters.pop()
        elif sName == 'li':
            self._insert_text("\n")
        elif sName == 'img':
            pass
        elif sName == 'body':
            pass
        elif sName == 'html':
            pass
        elif sName == 'head':
            pass
        elif sName == 'a':
            pass
        elif sName in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if not self._oIter.starts_line():
                self._insert_text("\n")
        else:
            warnings.warn("Unhandled element '%s'" % sName)
        self._end_span()

class HTMLTextView(gtk.TextView):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """TextView subclass to display HTML"""
    __gtype_name__ = 'HTMLTextView'
    __gsignals__ = {
        'url-clicked': (gobject.SIGNAL_RUN_LAST, None, (str, str)),
        # href, type
    }

    def __init__(self):
        gtk.TextView.__init__(self)
        self.set_wrap_mode(gtk.WRAP_CHAR)
        self.set_editable(False)
        self._bChangedCursor = False
        self.connect("motion-notify-event", self.__motion_notify_event)
        self.connect("leave-notify-event", self.__leave_event)
        self.connect("enter-notify-event", self.__motion_notify_event)
        self.set_pixels_above_lines(3)
        self.set_pixels_below_lines(3)

    # pylint: disable-msg=W0613
    # oEvent needed by function signature
    def __leave_event(self, oWidget, oEvent):
        """Cursor has left the widget."""
        if self._bChangedCursor:
            oWindow = oWidget.get_window(gtk.TEXT_WINDOW_TEXT)
            oWindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._bChangedCursor = False

    def __motion_notify_event(self, oWidget, oEvent):
        """Change the cursor if the pointer is over a link"""
        # pylint: disable-msg=W0612
        # We delibrately ignore oIgnore
        iXPos, iYPos, oIgnore = oWidget.window.get_pointer()
        iXPos, iYPos = oWidget.window_to_buffer_coords(gtk.TEXT_WINDOW_TEXT,
                iXPos, iYPos)
        aTags = oWidget.get_iter_at_location(iXPos, iYPos).get_tags()
        for oTag in aTags:
            if getattr(oTag, 'is_anchor', False):
                bOverAnchor = True
                break
        else:
            bOverAnchor = False
        if not self._bChangedCursor and bOverAnchor:
            oWindow = oWidget.get_window(gtk.TEXT_WINDOW_TEXT)
            oWindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
            self._bChangedCursor = True
        elif self._bChangedCursor and not bOverAnchor:
            oWindow = oWidget.get_window(gtk.TEXT_WINDOW_TEXT)
            oWindow.set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
            self._bChangedCursor = False
        return False

    # pylint: enable-msg=W0613

    def display_html(self, fHTMLInput):
        """Displa the HTML from the file-like object fHTMLInput"""
        oBuffer = self.get_buffer()
        oEndOfBuf = oBuffer.get_end_iter()
        oParser = xml.sax.make_parser()
        oParser.setContentHandler(HtmlHandler(self, oEndOfBuf))
        # Don't try and follow external references
        oParser.setFeature(xml.sax.handler.feature_external_ges, False)
        oParser.parse(fHTMLInput)

        if not oEndOfBuf.starts_line():
            oBuffer.insert(oEndOfBuf, "\n")

if gobject.pygtk_version < (2, 8):
    gobject.type_register(HTMLTextView)

class HTMLViewDialog(SutekhDialog):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Dialog Window that wraps the HTMLTextView

       Used to show HTML Manuals in Sutekh.
       """

    _sError = """<html>
    <body>
    <h1>Resource not found</h1>
    <p>Unable to load the resource %(missing)s</p>
    </body>
    </html>
    """

    def __init__(self, oParent, fInput):
        super(HTMLViewDialog, self).__init__('Help', oParent,
                oButtons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oDirButtons = gtk.HButtonBox()
        self._oBackButton = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self._oBackButton.connect('pressed', self._go_back)
        self._oForwardButton = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self._oForwardButton.connect('pressed', self._go_forward)
        oDirButtons.pack_start(self._oBackButton)
        oDirButtons.pack_start(self._oForwardButton)
        self._oBackButton.set_sensitive(False)
        self._oForwardButton.set_sensitive(False)
        self._fCurrent = fInput
        self._aPastUrls = []
        self._aFutureUrls = []
        self.vbox.pack_start(oDirButtons, False, False)
        self._oHTMLTextView = HTMLTextView()
        self._oView = AutoScrolledWindow(self._oHTMLTextView)
        self.set_default_size(400, 600)
        self._oHTMLTextView.display_html(fInput)
        self.vbox.pack_start(self._oView, True,
                True)
        self._oHTMLTextView.connect('url-clicked', self._url_clicked)
        self.connect('response', lambda x, but: self.hide())
        self.show_all()

    def _update_view(self):
        """Redraw the pane with the contents of self._fCurrent"""
        self._fCurrent.seek(0)
        self._oView.remove(self._oHTMLTextView)
        self._oHTMLTextView = HTMLTextView()
        self._oHTMLTextView.display_html(self._fCurrent)
        self._oHTMLTextView.connect('url-clicked', self._url_clicked)
        self._oView.add(self._oHTMLTextView)
        if len(self._aPastUrls) > 0:
            self._oBackButton.set_sensitive(True)
        else:
            self._oBackButton.set_sensitive(False)
        if len(self._aFutureUrls) > 0:
            self._oForwardButton.set_sensitive(True)
        else:
            self._oForwardButton.set_sensitive(False)
        self.show_all()

    def show_page(self, fInput):
        """Display the html file in fInput in the current window."""
        self._aPastUrls.append(self._fCurrent)
        self._aFutureUrls = [] # Forward history is lost
        self._fCurrent = fInput
        self._update_view()

    # pylint: disable-msg=W0613
    # oWidget, oType required by function signature
    def _url_clicked(self, oWidget, sUrl, oType):
        """Update the HTML widget with the new url"""
        sResource = '/docs/%s' % sUrl
        if resource_exists('sutekh', sResource):
            fInput = resource_stream('sutekh', sResource)
        else:
            sError = self._sError % { 'missing' : sUrl }
            fInput = StringIO(sError)
        self.show_page(fInput)

    def _go_back(self, oWidget):
        """Go backwards through the list of visited urls"""
        if len(self._aPastUrls) == 0:
            return
        self._aFutureUrls.append(self._fCurrent)
        self._fCurrent = self._aPastUrls.pop()
        self._update_view()

    def _go_forward(self, oWidget):
        """Go forward through the list of visited urls"""
        if len(self._aFutureUrls) == 0:
            return
        self._aPastUrls.append(self._fCurrent)
        self._fCurrent = self._aFutureUrls.pop()
        self._update_view()
