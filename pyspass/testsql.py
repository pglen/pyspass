#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function

import os, sys, getopt, signal, select, socket, time, struct
import random, stat

from mainwin import  *
from pgutil import  *

import pgpasql

import pypacker

if __name__ == '__main__':

    pgsql = pgpasql.pgpasql("testcomp.sqlt")
    #print(pgsql)

    mydata = ["1", 2, "3"]
    pb  = pypacker.packbin()

    arr = []
    cnt = 0
    for aa in range(100):
        kkk = str(uuid.uuid4())
        mydata.append("hello %d" % cnt)
        newdata  = pb.encode_data("", mydata)
        pgsql.putuni(kkk, newdata)
        arr.append(kkk)
        cnt += 10

    pgsql.putuni(arr[1], "another hello %d" % cnt)

    # read it
    arr2 = pgsql.getunikeys(0, 10)
    print(arr2)


# EOF

