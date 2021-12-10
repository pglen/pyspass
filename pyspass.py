#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function

import os, sys, getopt, signal, select, socket, time, struct
import random, stat

from mainwin import  *
from pgutil import  *

import pgpasql

# ------------------------------------------------------------------------
# Globals

# Version of the program
version = "0.50"

# ------------------------------------------------------------------------

def phelp():

    print()
    print( "Usage: " + os.path.basename(sys.argv[0]) + " [options]")
    print()
    print( "Options:    -d level  - Debug level 0-10")
    print( "            -v        - Verbose")
    print( "            -V        - Version")
    print( "            -q        - Quiet")
    print( "            -h        - Help")
    print()
    sys.exit(0)

# ------------------------------------------------------------------------
def pversion():
    print( os.path.basename(sys.argv[0]), "Version", version)
    sys.exit(0)

    # option, long_option,  var_name,   initial_value, function
optarrlong = \
    ["p:",    "port",        "port",     9999,           None],      \
    ["v",     "verbose",     "verbose",  0,              None],      \
    ["q",     "quiet",       "quiet",    0,              None],      \
    ["t",     "test",        "test",     0,              None],      \
    ["V",     "version",     None,       None,           pversion],  \
    ["h",     "help",        None,       None,           phelp],     \

conf = ConfigLong(optarrlong)

if __name__ == '__main__':

    #global mw

    args = conf.comline(sys.argv[1:])
    if conf.err:
        print(conf.err)
        sys.exit(1)

    #conf.printvars()
    pgsql = pgpasql.pgpasql("testdata.sqlt")
    mw = MainWin(pgsql)
    Gtk.main()
    sys.exit(0)

# EOF