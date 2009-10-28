# TestConsole.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""This module launches an interactive console.

   Its purpose is to provide an easy means to
   test the environment created by a py2exe build.
   """

if __name__ == "__main__":
    import code
    # pylint: disable-msg=C0103
    # pylint thinks this should be a constant
    console = code.InteractiveConsole()
    console.interact()
