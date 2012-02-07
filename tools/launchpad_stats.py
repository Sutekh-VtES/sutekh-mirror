#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar@gmail.com>
# GPL - see license file for details

from launchpadlib.launchpad import Launchpad

sApp = "sutekh-stats"
sTeam = "sutekh"

lp = Launchpad.login_anonymously(sApp)
team = lp.people[sTeam]

print "Showing download stats for team Sutekh's PPAs"
print "---------------------------------------------"

for ppa in team.ppas:
    print "%s/%s:" % (sTeam, ppa.name)
    binaries = ppa.getPublishedBinaries()
    for bin in binaries:
        print "  %s (%s):" % (bin.binary_package_name,
                              bin.binary_package_version)
        total = bin.getDownloadCount()
        stats = bin.getDailyDownloadTotals()
        print "    Total:", total
        for date in sorted(stats.keys()):
            print "    %s: %d" % (date, stats[date])

print "---------------------------------------------"
