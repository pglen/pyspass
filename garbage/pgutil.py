#!/usr/bin/env python

import os, sys, glob, getopt, time, string, signal, stat, shutil
import traceback

#import warnings; warnings.simplefilter("ignore");
#import gtk; warnings.simplefilter("default")

# ------------------------------------------------------------------------
# Handle command line. Interpret optarray and decorate the class

class Config:

    def __init__(self, optarr):
        self.optarr = optarr

    def comline(self, argv):
        optletters = ""
        for aa in self.optarr:
            if aa[0] in optletters:
                print( "Warning: duplicate option", "'" + aa[0] + "'")
            optletters += aa[0]
        #print( optletters    )

        # Create defaults:
        for bb in range(len(self.optarr)):
            if self.optarr[bb][1]:
                # Coerse type
                if type(self.optarr[bb][2]) == type(0):
                    self.__dict__[self.optarr[bb][1]] = int(self.optarr[bb][2])
                if type(self.optarr[bb][2]) == type(""):
                    self.__dict__[self.optarr[bb][1]] = str(self.optarr[bb][2])
        try:
            opts, args = getopt.getopt(argv, optletters)
        except getopt.GetoptError as err:
            print( "Invalid option(s) on command line:", err)
            return ()

        #print( "opts", opts, "args", args)
        for aa in opts:
            for bb in range(len(self.optarr)):
                if aa[0][1] == self.optarr[bb][0][0]:
                    #print( "match", aa, self.optarr[bb])
                    if len(self.optarr[bb][0]) > 1:
                        #print( "arg", self.optarr[bb][1], aa[1])
                        if self.optarr[bb][2] != None:
                            if type(self.optarr[bb][2]) == type(0):
                                self.__dict__[self.optarr[bb][1]] = int(aa[1])
                            if type(self.optarr[bb][2]) == type(""):
                                self.__dict__[self.optarr[bb][1]] = str(aa[1])
                    else:
                        #print( "set", self.optarr[bb][1], self.optarr[bb][2])
                        if self.optarr[bb][2] != None:
                            self.__dict__[self.optarr[bb][1]] = 1
                        #print( "call", self.optarr[bb][3])
                        if self.optarr[bb][3] != None:
                            self.optarr[bb][3]()
        return args

# ------------------------------------------------------------------------
# Print( an exception as the system would print it)

def print_exception(xstr):
    cumm = xstr + " "
    a,b,c = sys.exc_info()
    if a != None:
        cumm += str(a) + " " + str(b) + "\n"
        try:
            #cumm += str(traceback.format_tb(c, 10))
            ttt = traceback.extract_tb(c)
            for aa in ttt:
                cumm += "File: " + os.path.basename(aa[0]) + \
                        " Line: " + str(aa[1]) + "\n" +  \
                    "   Context: " + aa[2] + " -> " + aa[3] + "\n"
        except:
            print( "Could not print trace stack. ", sys.exc_info())
    print( cumm)

# ------------------------------------------------------------------------
# Never mind

def cmp(aa, bb):
    aaa = os.path.basename(aa);  bbb = os.path.basename(bb)
    pat = re.compile("[0-9]+")
    ss1 = pat.search(aaa)
    ss2 = pat.search(bbb)

    if(ss1 and ss2):
        aaaa = float(aaa[ss1.start(): ss1.end()])
        bbbb = float(bbb[ss2.start(): ss2.end()])
        #print( aaa, bbb, aaaa, bbbb)
        if aaaa == bbbb:
            return 0
        elif aaaa < bbbb:
            return -1
        elif aaaa > bbbb:
            return 1
        else:
            #print( "crap")
            pass
    else:
        if aaa == bbb:
            return 0
        elif aaa < bbb:
            return -1
        elif aaa > bbb:
            return 1
        else:
            #print( "crap")
            pass

# ------------------------------------------------------------------------
# Show a regular message:

def message(strx, title = None, icon = gtk.MESSAGE_INFO):

    dialog = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT,
        icon, gtk.BUTTONS_CLOSE, strx)

    if title:
        dialog.set_title(title)
    else:
        dialog.set_title("ePub Reader")

    # Close dialog on user response
    dialog.connect("response", lambda d, r: d.destroy())
    dialog.show()

# -----------------------------------------------------------------------
# Sleep just a little, but allow the system to breed

def  usleep(msec):

    got_clock = time.clock() + float(msec) / 1000
    #print( got_clock)
    while True:
        if time.clock() > got_clock:
            break
        gtk.main_iteration_do(False)

# -----------------------------------------------------------------------
# Call func with all processes, func called with stat as its argument
# Function may return True to stop iteration

def withps(func, opt = None):

    ret = False
    dl = os.listdir("/proc")
    for aa in dl:
        fname = "/proc/" + aa + "/stat"
        if os.path.isfile(fname):
            ff = open(fname, "r").read().split()
            ret = func(ff, opt)
        if ret:
            break
    return ret

# ------------------------------------------------------------------------
# Find

def find(self):

    head = "Find in text"

    dialog = gtk.Dialog(head,
                   None,
                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.set_default_response(gtk.RESPONSE_ACCEPT)

    try:
        dialog.set_icon_from_file("epub.png")
    except:
        print( "Cannot load find dialog icon", sys.exc_info())

    self.dialog = dialog

    # Spacers
    label1 = gtk.Label("   ");  label2 = gtk.Label("   ")
    label3 = gtk.Label("   ");  label4 = gtk.Label("   ")
    label5 = gtk.Label("   ");  label6 = gtk.Label("   ")
    label7 = gtk.Label("   ");  label8 = gtk.Label("   ")

    warnings.simplefilter("ignore")
    entry = gtk.Entry();
    warnings.simplefilter("default")
    entry.set_text(self.oldfind)

    entry.set_activates_default(True)

    dialog.vbox.pack_start(label4)

    hbox2 = gtk.HBox()
    hbox2.pack_start(label6, False)
    hbox2.pack_start(entry)
    hbox2.pack_start(label7, False)

    dialog.vbox.pack_start(hbox2)

    dialog.checkbox = gtk.CheckButton("Search _Backwards")
    dialog.checkbox2 = gtk.CheckButton("Case In_sensitive")
    dialog.vbox.pack_start(label5)

    hbox = gtk.HBox()
    #hbox.pack_start(label1);  hbox.pack_start(dialog.checkbox)
    #hbox.pack_start(label2);  hbox.pack_start(dialog.checkbox2)
    hbox.pack_start(label3);
    dialog.vbox.pack_start(hbox)
    dialog.vbox.pack_start(label8)

    label32 = gtk.Label("   ");  label33 = gtk.Label("   ")
    label34 = gtk.Label("   ");  label35 = gtk.Label("   ")

    hbox4 = gtk.HBox()

    hbox4.pack_start(label32);
    dialog.vbox.pack_start(hbox4)

    dialog.show_all()
    response = dialog.run()
    self.srctxt = entry.get_text()

    dialog.destroy()

    if response != gtk.RESPONSE_ACCEPT:
        return None

    return self.srctxt, dialog.checkbox.get_active(), \
                dialog.checkbox2.get_active()

# ------------------------------------------------------------------------
# Count lead spaces

def leadspace(strx):
    cnt = 0;
    for aa in range(len(strx)):
        bb = strx[aa]
        if bb == " ":
            cnt += 1
        elif bb == "\t":
            cnt += 1
        elif bb == "\r":
            cnt += 1
        elif bb == "\n":
            cnt += 1
        else:
            break
    return cnt





