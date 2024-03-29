#!/usr/bin/env python

import sys, string, random, base64

import pyvpacker

from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Hash import MD2
from Crypto import Random

USE_HASH    = SHA256
DEF_ENCPASS = "12345678"

# Removed some punctuation chars, may be used as separators etc ...
# Do not restructure this after you created / used some data as
# this will change the calculated hashes.

#Punct = "!#$%&*+-/:;=?^_~"
#Punct = "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"
#Punct = "!#$%&*+-/:;=?^_~"

# Reduced for more compatibility
Punct = "%+-:;=_"

def gen_pass_hash(row, epass):

    ''' generate all in one step '''

    master = dec_pass(epass, DEF_ENCPASS)
    try:
        val =  int(row[2])
    except:
        val = 0
    str_org = row[0] + row[1] + master + str(val)
    ppp = gen_pass(str_org);  hhh = gen_hash(str_org)
    # Destroy sensitive info
    master = ""
    return ppp, hhh

def gen_hash(str_org):

    '''  Generate hash out of the passed string. '''

    #print("str_org", str_org)
    hh = USE_HASH.new(); hh.update(str_org.encode()); sss = hh.hexdigest()
    return sss

def gen_pass(strx):

    ''' Generate random looking pass; make first 2 characters lower and upper
        case letters. Some programs want an ascii beginning. Returns
        32 chars of random looking string. '''

    hh = SHA256.new(); hh.update(strx.encode())
    passgen = hh.hexdigest()

    # Make sure they are less than 255
    idl = string.ascii_lowercase * 2 + string.ascii_uppercase
    ids = string.ascii_lowercase * 3 + string.ascii_uppercase + string.digits + Punct * 2
    #print (len(ids), ids)

    xarr = []
    skip = 4
    for aa in range(skip//2):
        ss =  passgen[2*aa] +  passgen[2*aa+1]
        #print(ss, int(ss, 16))
        xarr.append(idl[int(ss, 16) % len(idl)])

    for aa in range(skip//2, len(passgen)//2):
        ss =  passgen[2*aa] +  passgen[2*aa+1]
        #print(ss, int(ss, 16))
        xarr.append(ids[int(ss, 16) % len(ids)])
    strr = "".join(xarr)

    #print ("xlen", len(passgen), "len:", len(strr), "strr", strr)
    return strr

def padx(strx):
    #print("padx", "'"+strx+"'")
    sss = strx + " " * (AES.block_size - len(strx) % AES.block_size)
    #print("sssx", "'"+sss+"'")
    return sss.encode()

def enc_pass(strx, passx):

    lenx = len(strx)
    passpad = padx(passx)
    iv = Random.get_random_bytes(AES.block_size)
    cipher = AES.new(passpad, AES.MODE_CBC, iv)
    msg = cipher.encrypt(padx(strx))
    hexx = base64.b64encode(msg).decode('cp437')
    #print("hexx", hexx)
    iv2 = base64.b64encode(iv).decode('cp437')
    ppp = pyvpacker.packbin().encode_data("", (lenx, iv2, hexx,))
    #print("encrypted:", ppp)
    return ppp

def dec_pass(strx, passx):

    ppp = pyvpacker.packbin().decode_data(strx)[0]
    passpad = padx(passx)
    uhexx   = base64.b64decode(ppp[2])
    #print("uhexx", uhexx)
    iv      = base64.b64decode(ppp[1])
    cipher = AES.new(passpad, AES.MODE_CBC, iv)
    msg = cipher.decrypt(uhexx).decode('cp437')[:ppp[0]]
    # Do not show ... this can be the password (debug only)
    #print("decrypted", msg)
    return msg


# EOF
