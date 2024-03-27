#!/usr/bin/env python

#from __future__ import absolute_import
#from __future__ import print_function

import sys, string, random, base64

from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto import Random

import pyvpacker

# Removed some punctuation chars, may be used as separators etc ...
# Do not restructure this after you created / used some data as
# this will change the calculated hashes.

#Punct = "!#$%&*+-/:;=?^_~"
#Punct = "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
#Punct = "!#$%&*+-/:;=?^_~"

# Reduced for more compatibility
Punct = "%+-:;=_"

def gen_pass(strx):

    hh = SHA256.new(); hh.update(strx.encode())
    passx = hh.hexdigest()

    # Make sure they are less than 255
    idl = string.ascii_lowercase * 2 + string.ascii_uppercase
    ids = string.ascii_lowercase * 2 + string.ascii_uppercase + string.digits + Punct * 2
    #print (len(ids), ids)

    xarr = []
    skip = 4
    for aa in range(skip//2):
        ss =  passx[2*aa] +  passx[2*aa+1]
        #print(ss, int(ss, 16))
        xarr.append(idl[int(ss, 16) % len(idl)])

    for aa in range(skip//2, len(passx)//2):
        ss =  passx[2*aa] +  passx[2*aa+1]
        #print(ss, int(ss, 16))
        xarr.append(ids[int(ss, 16) % len(ids)])
    strr = "".join(xarr)
    print ("xlen", len(passx), "len:", len(strr), "strr", strr)
    return strr

def padx(strx):
    #print("padx", "'"+strx+"'")
    sss = strx + " " * (AES.block_size - len(strx) % AES.block_size)
    #print("sssx", "'"+sss+"'")
    return sss

def enc_pass(strx, passx):

    lenx = len(strx)
    passpad = padx(passx)
    iv = Random.get_random_bytes(AES.block_size)
    cipher = AES.new(passpad, AES.MODE_CBC, iv)
    msg = cipher.encrypt(padx(strx))
    hexx = base64.b64encode(msg).decode('cp437')
    #print("hexx", hexx)
    iv2 = base64.b64encode(iv).decode('cp437')
    ppp = pypacker.packbin().encode_data("", (lenx, iv2, hexx,))
    print("encrypted", ppp)
    return ppp

def dec_pass(strx, passx):

    ppp = pypacker.packbin().decode_data(strx)[0]
    print(ppp)
    passpad = padx(passx)

    uhexx   = base64.b64decode(ppp[2])
    #print("uhexx", uhexx)
    iv      = base64.b64decode(ppp[1])

    cipher = AES.new(passpad, AES.MODE_CBC, iv)
    msg = cipher.decrypt(uhexx).decode('cp437')[:ppp[0]]
    print("decrypted", msg)
    return msg

# EOF
