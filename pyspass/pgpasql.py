#!/usr/bin/env python3

#from __future__ import absolute_import
#from __future__ import print_function

import sys, os, time, sqlite3, traceback

# Replaces g c o n f, so it is less platforrm dependent

base = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(base))

#print(sys.path)

import pgutil

class pgpasql():

    def __init__(self, file):

        #self.take = 0

        try:
            self.conn = sqlite3.connect(file)
        except:
            print("Cannot open/create db:", file, sys.exc_info())
            raise
            #return
        try:
            self.c = self.conn.cursor()
            self.c.execute("PRAGMA synchronous=OFF")

            # Create table
            self.c.execute("create table if not exists config \
             (pri INTEGER PRIMARY KEY, key text, val text, val2 text, val3 text, val4 text, val5 text, val6 text)")
            self.c.execute("create index if not exists iconfig on config (key)")
            self.c.execute("create index if not exists pconfig on config (pri)")

            self.c.execute("create table if not exists udata \
                     (pri INTEGER PRIMARY KEY, key text, val text)")
            self.c.execute("create index if not exists pudata on udata (key)")

            # Save (commit) the changes
            self.conn.commit()
        except:
            print("Cannot crate tables", sys.exc_info())

        finally:
            # We close the cursor, we are done with it
            #c.close()
            pass

    # --------------------------------------------------------------------

    def   getunikeys(self, startx=-1, endx=-1):
        try:
            #c = self.conn.cursor()
            if startx < 0:
                self.c.execute("select key from udata")
            else:
                self.c.execute("select key from udata limit ? offset ? ", (endx, startx))

            rr = self.c.fetchall()
        except:
            print("Cannot get sql data", sys.exc_info())
            return
        finally:
            #c.close
            pass
        return rr


    # Return None if no data

    def   get(self, kkk):
        try:
            #c = self.conn.cursor()
            if os.name == "nt":
                self.c.execute("select * from udata where key = ?", (kkk,))
            else:
                self.c.execute("select * from udata by pudata where key = ?", (kkk,))
            rr = self.c.fetchone()
        except:
            print("get: cannot get sql data", sys.exc_info())
            rr = None
        finally:
            #c.close
            pass
        if rr:
            return rr[2:]
        else:
            return None

    # ------------------------------------------------------------------------------

    def   getuni(self, kkk):
        try:
            #c = self.conn.cursor()
            if os.name == "nt":
                self.c.execute("select * from udata where key = ?", (kkk,))
            else:
                self.c.execute("select * from udata indexed by pudata where key = ?", (kkk,))
            rr = self.c.fetchone()
        except:
            print("getuni: cannot get sql data", sys.exc_info())
            rr = None
        finally:
            #c.close
            pass
        if rr:
            return rr[2:]
        else:
            return None

    def   putuni(self, key, val):

        #got_clock = time.clock()

        ret = True
        try:
            #c = self.conn.cursor()
            if os.name == "nt":
                self.c.execute("select * from udata where key == ?", (key,))
            else:
                self.c.execute("select * from udata indexed by pudata where key == ?", (key,))
            rr = self.c.fetchall()
            if rr == []:
                #print "inserting"
                self.c.execute("insert into udata (key, val) \
                    values (?, ?)", (key, val))
            else:
                #print "updating"
                if os.name == "nt":
                    self.c.execute("update udata set val = ? where key = ?",\
                                                                        (val, key))
                else:
                    self.c.execute("update udata indexed by pudata " +
                                    "set val = ? where key = ?",\
                                                            (val, key))
            self.conn.commit()
        except:
            print("putuni: cannot put sql data", sys.exc_info())
            print(traceback.format_exc())

            #pgutil.print_exception("on put")
            ret = False
        finally:
            #c.close
            pass

        #self.take += time.clock() - got_clock

        return ret

    # --------------------------------------------------------------------
    # Return False if cannot put data

    def   put(self, key, val, val2, val3, val4, val5, val6):

        #got_clock = time.clock()

        ret = True
        try:
            #c = self.conn.cursor()
            if os.name == "nt":
                self.c.execute("select * from config where key == ?", (key,))
            else:
                self.c.execute("select * from config indexed by iconfig where key == ?", (key,))
            rr = self.c.fetchall()
            if rr == []:
                #print "inserting"
                self.c.execute("insert into config (key, val, val2, val3, val4, val5, val6) \
                    values (?, ?, ?, ?, ?, ?, ?)", (key, val, val2, val3, val4, val5, val6 ))
            else:
                #print "updating"
                if os.name == "nt":
                    self.c.execute("update config set val = ?, val2 = ?, val3 = ?, val4 = ?, val5 = ? , val6 = ? where key = ?",\
                                     (val, val2, val3, val4, val5, val6, key))
                else:
                    self.c.execute("update config indexed by iconfig " +
                                    "set val = ?, val2 = ?, val3 = ?, val4 = ?, val5 = ? , val6 = ? where key = ?",\
                                         (val, val2, val3, val4, val5, val6, key))
            self.conn.commit()
        except:
            print("Cannot put sql data", sys.exc_info())
            print(traceback.format_exc())

            #pgutil.print_exception("on put")
            ret = False
        finally:
            #c.close
            pass

        #self.take += time.clock() - got_clock

        return ret

    # --------------------------------------------------------------------
    # Get All

    def   getall(self):
        try:
            #c = self.conn.cursor()
            self.c.execute("select * from config")
            rr = self.c.fetchall()
        except:
            print("Cannot get sql data", sys.exc_info())
        finally:
            #c.close
            pass
        return rr

    def   getallkeys(self):
        try:
            #c = self.conn.cursor()
            self.c.execute("select key from config")
            rr = self.c.fetchall()
        except:
            print("Cannot get sql data", sys.exc_info())
        finally:
            #c.close
            pass
        return rr

    def   rmone(self, kkk):
        print("removing one:", "'" + kkk + "'" )
        rr = None
        try:
            #c = self.conn.cursor()
            self.c.execute("delete from udata where key == ?", (kkk,))
            self.conn.commit()
            rr = self.c.fetchone()
        except:
            print("Cannot delete sql data for", kkk, sys.exc_info())
        finally:
            #c.close
            pass
        if rr:
            return rr[1]
        else:
            return None

    # --------------------------------------------------------------------
    # Return None if no data

    def   rmall(self):
        print("removing all")
        try:
            self.c.execute("delete from udata")
            #c = self.conn.cursor()
            self.conn.commit()
            rr = self.c.fetchone()
        except:
            print("Cannot delete sql data", sys.exc_info())
        finally:
            #c.close
            pass
        if rr:
            return rr[1]
        else:
            return None

# EOF