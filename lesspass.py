#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import string

from Crypto.Hash import SHA256

#import Crypto
#print(Crypto.Hash.__doc__)

# Removed some punctuation chars, may be used as separators etc ...
# Do not restructure this after you used some data

#Punct = "!#$%&*+-/:;=?^_~"
Punct = "!#$%&*+-/:;=?^_~"

# Reduced them for more compatibility
#Punct = "%+-/:;=_"

def gen_pass(strx):

    hh = SHA256.new(); hh.update(strx.encode())
    passx = hh.hexdigest()

    # Make sure thay are less than 255
    ids = string.ascii_lowercase * 3 + string.ascii_uppercase * 2 + string.digits * 2 + Punct * 2
    #print (len(ids), ids)

    strx = ""
    for aa in range(len(passx)//2):
        ss =  passx[2*aa] +  passx[2*aa+1]
        #print(ss, int(ss, 16))
        strx += ids[int(ss, 16) % len(ids)]

    #print (len(strx), strx)
    return strx
