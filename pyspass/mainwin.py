#!/usr/bin/env python

import os, sys, getopt, signal, random, time, warnings, string
import qrcode, uuid

from PIL import Image, ImageFilter, ImageOps

from Crypto.Hash import MD2
from Crypto.Hash import SHA256

import  lesspass

#from pymenu import  *

import  pyvpacker
from    pgutil import  *
#from    pgui import  *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Pango

DEF_LEN     = 14            # Default pass len
MAX_TRY     =  4            # Maximum pass try
MASTER_TEMPLATE = "e86c1b3c-eb7c-11ee-9b87-4b6ca61ffd8e"

(F_DOM, F_LOG,
F_SER, F_HASH,
F_NOTE, F_ID) = list(range(6))

# Make even and odd flags for obfuscation. This way boolean desision
# is made on an integer instead of 0 and 1

for aa in range(6):
    r1 = random.randint(0, 100000); FLAG_ON  =  (r1 // 2) * 2
    r2 = random.randint(0, 100000); FLAG_OFF =  (r2 // 2) * 2 + 1
    # Unlikely, but catch it
    if FLAG_ON != FLAG_OFF:
        break

#print("flags:", FLAG_ON, FLAG_OFF)

# Field names
fields = ("Site", "Login", "Serial", "Pass", "Override",
            "Pass Len", "Notes",  "ChkSum", "UUID",  )

# Fields become editable (ordinal sensitive)
editable  = (True, True, True, False, True,
            True, True,  False, False,  )

# Fields centerred  (ordinal sensitive)
centered  = ( False, False, True, False, False,
                True, False,  False, False,  )

# Placeholder
passx  =  " - " * 6 + "   "

# No blank sheet
initial =   [ \
                (MASTER_TEMPLATE, "template.com", "username"),
                 ("",             "example.com",  "username"),
                 ("",             "domain.com",   "username"),
            ]

newdata =   [ \
                "HostID", "LoginName",  "0", passx, passx, str(DEF_LEN),
                    "Notes Here", "ChkSum", "ID",
            ]

gl_try  = 0
gl_cnt = 0
verbose = 0

# ------------------------------------------------------------------------

class MainWin(Gtk.Window):

    def __init__(self, sqlfile, pgdebug = 0):

        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.sql = sqlfile
        self.pgdebug = pgdebug
        self.master = FLAG_OFF
        self.alldat = []
        # So this is never empty, add bogus default
        self.master_save =  lesspass.enc_pass(lesspass.DEF_ENCPASS, lesspass.DEF_ENCPASS)
        self.ini = False
        self.pb = pyvpacker.packbin()
        self.noimg = None
        self.loadicon()
        self.autolog = 0
        self.dx = 0; self.dy = 0

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        #print("pgdebug", self.pgdebug)
        self.set_title("PysPass Password Manager")
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

        #ic = Gtk.Image(); ic.set_from_stock(Gtk.STOCK_DIALOG_INFO, Gtk.ICON_SIZE_BUTTON)
        #window.set_icon(ic.get_pixbuf())

        www = Gdk.Screen.width(); hhh = Gdk.Screen.height();

        disp2 = Gdk.Display()
        disp = disp2.get_default()
        #print( disp)
        scr = disp.get_default_screen()
        ptr = disp.get_pointer()
        mon = scr.get_monitor_at_point(ptr[1], ptr[2])
        geo = scr.get_monitor_geometry(mon)
        www = geo.width; hhh = geo.height
        xxx = geo.x;     yyy = geo.y

        # Resort to old means of getting screen w / h
        if www == 0 or hhh == 0:
            www = Gdk.screen_width(); hhh = Gdk.screen_height();

        if www / hhh > 2:
            self.set_default_size(6*hhh/8, 5*hhh/8)
        else:
            self.set_default_size(6*www/8, 6*hhh/8)

        self.connect("destroy", self.onexit)
        self.connect("key-press-event", self.key_press_event)
        self.connect("button-press-event", self.button_press_event)
        self.connect("motion-notify-event", self.motion_notify_event)

        try:
            #self.set_icon_from_file("icon.png")
            self.set_icon(self.noimg.get_pixbuf())
        except:
            pass

        vbox = Gtk.VBox(); hbox4 = Gtk.HBox(); hbox5 = Gtk.HBox()

        #merge = Gtk.UIManager()
        ##self.mywin.set_data("ui-manager", merge)
        #
        #aa = create_action_group(self)
        #merge.insert_action_group(aa, 0)
        #self.add_accel_group(merge.get_accel_group())
        #
        #merge_id = merge.new_merge_id()
        #
        #try:
        #    mergeid = merge.add_ui_from_string(ui_info)
        #except GLib.GError as msg:
        #    print("Building menus failed: %s" % msg)

        hbox4.pack_start(Gtk.Label("  "), 0, 0, 2)

        lab2 = Gtk.Label("  Status:   ");  hbox4.pack_start(lab2, 0, 0, 0)
        self.status = Gtk.Label.new_with_mnemonic("Idle.");
        self.status.set_xalign(0)
        hbox4.pack_start(self.status, 1, 1, 0)
        self.collab = Gtk.Label("   ")
        self.collab.override_background_color(Gtk.StateFlags.NORMAL,
                                                    Gdk.RGBA(.99, .1, .1))
        hbox4.pack_start(self.collab, 0, 0, 0)

        tt = type(""); fff = []
        for ccc in range(len(fields)):
            fff.append(tt)
        self.model = Gtk.TreeStore(*fff)
        self.tree = Gtk.TreeView(self.model)
        self.tree.connect("cursor-changed", self.row_activate)
        self.tree.connect("key-press-event", self.onTreeNavigateKeyPress)
        self.tree.connect("button-press-event", self.tree_press_event)

        self.tree.set_enable_search(False)

        self.cells = []; cntf = 0
        for aa in fields:
            col = Gtk.TreeViewColumn(aa, self.cellx(cntf), text=cntf)
            col.set_resizable(True)
            self.tree.append_column(col)
            cntf += 1

        self.ini = self.load_data()
        self.data_to_tree()

        if self.ini:
            self.labn = Gtk.Label.new_with_mnemonic("  New master Pass:")
            self.labn.set_markup_with_mnemonic(" <span foreground=\"#AA0000\"> !!! Ne_w Master Pass: !!! </span>")
        else:
            self.labn = Gtk.Label.new_with_mnemonic("  Master Pa_ss:")

        hbox4.pack_start(self.labn, 0, 0, 4)

        self.input = Gtk.Entry()
        self.input.connect("activate", self.activate_edit)
        self.input.set_visibility(False)
        self.labn.set_mnemonic_widget(self.input)
        hbox4.pack_start(self.input, 0, 0, 4)

        self.input2 = Gtk.Entry()
        self.input2.set_visibility(False)
        self.input2.connect("activate", self.activate2)

        if self.ini:
            prom = "_Confirm:"
        else:
            prom = ""
            self.input2.hide()

        self.labconf = Gtk.Label.new_with_mnemonic(prom)
        self.labconf.set_mnemonic_widget(self.input2)

        hbox4.pack_start(self.labconf, 0, 0, 2)
        hbox4.pack_start(self.input2, 0, 0, 2)

        if self.ini:
            self.buttA = Gtk.Button.new_with_mnemonic("   Create Ma_ster Pass   ")
        else:
            self.buttA = Gtk.Button.new_with_mnemonic("   Unlo_ck   ")

        self.buttA.connect("clicked", self.master_new)
        hbox4.pack_start(self.buttA, False, 0, 2)

        #buttB = Gtk.Button.new_with_mnemonic("   Lock _Data  ")
        #buttB.connect("clicked", self.master_lock)
        #hbox4.pack_start(buttB, False, 0, 2)

        hbox4.pack_start(Gtk.Label(" "), 0, 0, 0)

        butt2 = Gtk.Button.new_with_mnemonic("    E_xit    ")
        butt2.connect("clicked", self.onexit, self)
        hbox4.pack_start(butt2, False, 0, 0)

        lab2 = Gtk.Label("   ");  hbox4.pack_start(lab2, 0, 0, 2)

        #hbox2 = Gtk.HBox()
        #lab3 = Gtk.Label("aa");  hbox2.pack_start(lab3, 0, 0, 0)
        #lab4 = Gtk.Label("");  hbox2.pack_start(lab4, 0, 0, 0)
        #vbox.pack_start(hbox2, False, 0, 0)

        hbox3 = Gtk.HBox()
        #self.edit = SimpleEdit();
        #self.edit = Gtk.Label(" L1 ")

        qq = qrcode.make()
        xx =  ImageOps.grayscale(qq)
        qqq = xx.convert("RGB")
        dd = self.image2pixbuf(qqq)

        self.edit = Gtk.Image()
        self.edit2 = Gtk.Image()
        self.edit3 = Gtk.Image()
        self.edit4 = Gtk.Image()
        self.apply_qr("12345678", "password", "override", "host.none")
        self.pad = Gtk.Notebook()

        labx = Gtk.Label("Site"); labx.set_tooltip_text("QR code for selected site")
        self.pad.append_page(self.edit4, labx)
        laba = Gtk.Label("Login"); laba.set_tooltip_text("QR code for selected login")
        self.pad.append_page(self.edit, laba)
        laba2 = Gtk.Label("Pass"); laba2.set_tooltip_text("QR code for selected password")
        self.pad.append_page(self.edit2, laba2)
        laba3 = Gtk.Label("Over"); laba3.set_tooltip_text("QR code for selected override")
        self.pad.append_page(self.edit3, laba3)

        self.hpane = Gtk.HPaned()
        self.hpane.set_position(300)

        self.scroll = Gtk.ScrolledWindow()
        #self.scroll.add_with_viewport(self.tree)
        self.scroll.add(self.tree)

        #vbox3 = Gtk.VBox()
        #vbox3.pack_start(self.scroll, 1, 1, 0)

        hbox6 = Gtk.HBox()

        hbox6.pack_start(Gtk.Label("  "), 0, 0, 2)

        butt1 = Gtk.Button.new_with_mnemonic("   Copy Lo_gin  ")
        butt1.connect("clicked", self.copy)
        hbox6.pack_start(butt1, 0, 0, 2)
        butt2 = Gtk.Button.new_with_mnemonic("   Copy P_ass  ")
        butt2.connect("clicked", self.copy2)
        hbox6.pack_start(butt2, 0, 0, 2)
        butt2a = Gtk.Button.new_with_mnemonic("   Copy O_verride  ")
        butt2a.connect("clicked", self.copy3)
        hbox6.pack_start(butt2a, 0, 0, 2)

        #hbox6.pack_start(Gtk.Label(" "), 0, 0, 2)

        buttc = Gtk.CheckButton.new_with_mnemonic("Allow A_dmin")
        buttc.connect("toggled", self.allow_adm)
        hbox6.pack_start(buttc, 0, 0, 2)

        self.butt_new = Gtk.Button.new_with_mnemonic("  _New Row  ")
        self.butt_new.set_sensitive(False)
        self.butt_new.connect("clicked", self.add_newrow)
        hbox6.pack_start(self.butt_new, 0, 0, 2)

        self.butt_del = Gtk.Button.new_with_mnemonic("   Del _Row  ")
        self.butt_del.set_sensitive(False)
        self.butt_del.connect("clicked", self.del_row)
        hbox6.pack_start(self.butt_del, 0, 0, 2)

        self.butt_export = Gtk.Button.new_with_mnemonic("  Export  ")
        self.butt_export.set_sensitive(False)
        self.butt_export.connect("clicked", self.export)
        hbox6.pack_start(self.butt_export, 1, 1, 2)

        self.buttp = Gtk.CheckButton.new_with_mnemonic(" Show passes ")
        self.buttp.connect("toggled", self.show_passes)
        hbox6.pack_start(self.buttp, 0, 0, 2)

        hbox6.pack_start(Gtk.Label(" "), 0, 0, 2)

        self.hpane.add(self.scroll)
        self.hpane.add(self.pad)

        #for row in self.model:
        #    print(row[:])
        #print ("size", self.get_default_size())

        self.hpane.set_position(2 * self.get_default_size()[0] / 3)
        hbox3.pack_start(self.hpane, True, True, 6)

        vbox.pack_start(hbox5, False, False, 2)
        vbox.pack_start(hbox3, True, True, 2)
        vbox.pack_start(hbox6, 0, 0, 4)
        vbox.pack_start(hbox4, False, 0, 6)

        self.add(vbox)
        self.show_all()

        # Hide after general show
        if not self.ini:
            self.input2.hide()

        self.input.grab_focus_without_selecting()

        self.stat_time = 0
        GLib.timeout_add(1000, self.stat_timer)
        GLib.timeout_add(5000, self.autologout)

    def loadicon(self):
        base = os.path.dirname(os.path.realpath(__file__))
        self.noimg = Gtk.Image.new_from_file(base + os.sep + "noinfo.png")

    def run(self):
        Gtk.main()

    def motion_notify_event(self, win, event):
        #print("motion_notify_event", win, event)
        self.dx = self.dx - event.x
        self.dy = self.dy - event.y
        thresh = 3
        #print("motion:", self.dx, self.dy)
        if abs(self.dx) > thresh or abs(self.dy) > thresh:
            #print("Motion", self.dx, self.dy)
            self.autolog = 0
        self.dx = event.x; self.dy = event.y

    def _create_menuitem(self, string, action, arg = None):
        rclick_menu = Gtk.MenuItem(string)
        rclick_menu.connect("activate", action, string, arg);
        rclick_menu.show()
        return rclick_menu

    def menu_copy(self, menu, menutext, arg):
        #print("menu", menutext, arg)
        if arg == 0:
            pass
        elif arg == 1:
            self.copy2(0)
        elif arg == 2:
            self.copy3(0)
        elif arg == 3:
            self.copy(0)
        elif arg == 4:
            self.copy4(0)

    def tree_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == 3:
                #print("Right click")
                menu = Gtk.Menu()

                if self.master != FLAG_ON:
                    menu.append(self._create_menuitem("Must enter  master pass first", self.menu_copy, 0))
                else:
                    menu.append(self._create_menuitem("Copy Pass", self.menu_copy, 1))
                    menu.append(self._create_menuitem("Copy Override", self.menu_copy, 2))
                    menu.append(self._create_menuitem("Copy User (login) name", self.menu_copy, 3))
                    menu.append(self._create_menuitem("Copy domain name", self.menu_copy, 4))
                menu.popup_at_pointer(event)

    def show_passes(self, arg):
        flag = arg.get_active()
        self.input.set_visibility(flag)
        self.input2.set_visibility(flag)

    def allow_adm(self, arg):
        flag = arg.get_active()
        self.butt_new.set_sensitive(flag)
        self.butt_del.set_sensitive(flag)
        self.butt_export.set_sensitive(flag)

    def export(self, arg):
        #print("Export")
        if self.master != FLAG_ON:
            self.message("Cannot export if master key is not entered.")
            return

        fname = ""; progname = "prog.txt"
        for aa in range(10):
            fname =  "export_%d.txt" % aa
            #print(fname)
            if not os.path.isfile(fname):
                break

        #print("aa", aa)

        fp = open(fname, "wb")
        for aa in self.alldat:
            #print(aa)
            bstr = ", ".join(aa)
            fp.write(bstr.encode() + b"\n")

        fp.close()
        self.status.set_text("Exported Data to '%s'" % fname)
        self.stat_time = 5;

    def activate2(self, arg1):
        #print("activate2")
        self.master_unlock()

    def activate_edit(self, arg1):
        #print("activate_edit")
        if self.ini:
            #self.set_focus(self.input2)
            self.input2.grab_focus_without_selecting()

            return
        # Do not re lock / unlock from keyboard
        if self.master != FLAG_ON:
            self.master_unlock()

    def _pre_copy(self):
        if self.master != FLAG_ON:
            self.message("Cannot copy record if master key is not entered.")
            raise ValuError
        sel = self.tree.get_selection()
        tree, curr = sel.get_selected()
        if not curr:
            self.message("Please select a row to copy from.")
            raise ValuError
        return curr

    def copy(self, arg):
        try:
            curr = self._pre_copy()
        except:
            return
        self.status.set_text("Copied login name")
        self.stat_time = 5;
        ttt = self.tree.get_model().get_value(curr, 1)
        self.clipboard.set_text(ttt, len(ttt))

    def copy2(self, arg):
        try:
            curr = self._pre_copy()
        except:
            return
        self.status.set_text("Copied pass")
        self.stat_time = 5;
        ttt = self.tree.get_model().get_value(curr, 3)
        self.clipboard.set_text(ttt, len(ttt))

    def copy3(self, arg):
        try:
            curr = self._pre_copy()
        except:
            return
        self.status.set_text("Copied override")
        self.stat_time = 5;
        ttt = self.tree.get_model().get_value(curr, 4)
        self.clipboard.set_text(ttt, len(ttt))

    def copy4(self, arg):
        try:
            curr = self._pre_copy()
        except:
            return
        self.status.set_text("Copied override")
        self.stat_time = 5;
        ttt = self.tree.get_model().get_value(curr, 0)
        self.clipboard.set_text(ttt, len(ttt))

    def row_activate(self, arg1):
        sel = self.tree.get_selection()
        tree, curr = sel.get_selected()
        if not curr:
            return

        #print("row_activate",  curr)
        ppp = self.model.get_path(curr)
        row = self.model[ppp]
        self.apply_qr(row[1], row[3], row[4], row[0])
        if self.master == FLAG_ON:
            self.status.set_text("Selected site: '%s'" % row[0])
        self.stat_time = 4;

    def del_row(self, arg1):

        #print("del_row()", arg1)

        if self.master != FLAG_ON:
            self.message("Cannot delete record if master key is not entered.")
            return

        sel = self.tree.get_selection()
        tree, curr = sel.get_selected()
        if not curr:
            self.message("Please select a row to delete.")
            return

        id = tree.get_value(curr, 8)
        if id == MASTER_TEMPLATE:
            self.message("Cannot delete master template.")
            return

        #print("remove row", curr, id)
        for aa in range(len(self.alldat)):
            try:
                if self.alldat[aa][8] == id:
                    del self.alldat[aa]
                    self.sql.rmone(id)
                    # break # If multiple entries with the same ID, nuke em
            except:
                pass

        ret = tree.remove(curr)


    def add_newrow(self, arg1):

        global gl_cnt
        if self.master != FLAG_ON:
            self.message("Cannot add record if master key is not entered.")
            return

        #xlen = len(self.model)

        # Construct new
        ddd = newdata[:]
        ddd[0] = "HostID_%d" % (gl_cnt) ; gl_cnt += 1
        ddd[8] = str(uuid.uuid1())

        ppp, hhh = lesspass.gen_pass_hash(ddd, self.master_save)
        ddd[3] = ppp  #ppp[:int(ddd[5])] ;
        ddd[7] = hhh
        self.alldat.append(ddd)

        self.data_to_tree()
        self.save_row(ddd)

        sel = self.tree.get_selection()
        iter = self.model.get_iter_first()

        # Select last
        while True:
            iter2 =  self.model.iter_next(iter)
            if not iter2:
                break
            iter = iter2
        sel.select_iter(iter)

    def apply_qr(self, strx, passx, over, site):
        #print ("new QR", strx)

        qq =  qrcode.make(site, version=1)
        dd = self.image2pixbuf(qq)
        self.edit4.set_from_pixbuf(dd)

        if self.master != FLAG_ON:
            qq =  qrcode.make(strx, version=1)
            dd = self.image2pixbuf(qq)
            self.edit.set_from_pixbuf(dd)
            qq =  qrcode.make(passx, version=1)
            dd = self.image2pixbuf(qq)
            self.edit2.set_from_pixbuf(dd)
            qq =  qrcode.make(over, version=1)
            dd = self.image2pixbuf(qq)
            self.edit3.set_from_pixbuf(dd)
        else:
            self.edit.set_from_pixbuf(self.noimg.get_pixbuf())
            self.edit2.set_from_pixbuf(self.noimg.get_pixbuf())
            self.edit3.set_from_pixbuf(self.noimg.get_pixbuf())

    def image2pixbuf(self, im):
        """Convert Pillow image to GdkPixbuf"""
        qqq = im.convert("RGB")
        data = qqq.tobytes()
        ww, hh = qqq.size
        data2 = GLib.Bytes.new(data)
        pix = GdkPixbuf.Pixbuf.new_from_bytes(
                                    data2, GdkPixbuf.Colorspace.RGB,
                                                      False, 8, ww, hh, ww*3 )
        return pix

    def cellx(self, idx):
        cell = Gtk.CellRendererText()

        if centered[idx]:
            cell.set_property("alignment", Pango.Alignment.CENTER)
            cell.set_property("align-set", True)
            cell.set_alignment(0.5, 0.)

        cell.connect("edited", self.text_edited, idx)
        self.cells.append(cell)
        return cell

    def text_edited(self, widget, path, text, idx):

        if self.master != FLAG_ON:
            self.message("Cannot edit if master key is not entered.")
            return
        #print("edited", text, idx)

        # Changed?
        if  self.model[path][idx] == text:
            return

        if self.pgdebug > 1:
            print("text_edited()", path, self.model[path][idx], text)

        # Find backing data
        ddd =  None
        for aa in range(len(self.alldat)):
            if self.alldat[aa][8] ==  self.model[path][8]:
                #print("edited found:", aa)
                ddd = self.alldat[aa]
                break
        if not ddd:
            print("Internal error, no data backing found")
            return

        #row = self.model[path]

        if idx == 0 or idx == 1:
            # Re-generate this one
            ddd[idx] = text
            ppp, hhh = lesspass.gen_pass_hash(ddd, self.master_save)
            ddd[3] = ppp
            ddd[7] = hhh
            self.tree.get_columns()[0].queue_resize()
            self.tree.get_columns()[1].queue_resize()

        elif idx == 2:
            try:
                self.model[path][idx] = str(int(text))
            except:
                self.message("\nSerial field must be an integer.")
                return
            # Re-generate this one
            ddd[idx] = text
            ppp, hhh = lesspass.gen_pass_hash(ddd, self.master_save)
            ddd[3] = ppp
            ddd[7] = hhh
        elif idx == 5:
            try:
                val = str(int(text))
            except:
                self.message("\nLength field must be an integer.")
                return
            valx = int(text)
            if valx > 32 or valx < 6:
                self.message(
                "\nLength field must be beteen 6 and 32 .. default (%d) saved." % DEF_LEN)
                xval = str(DEF_LEN)

            ddd[idx] = str(valx)
            self.tree.get_columns()[3].queue_resize()
        elif idx == 4:
            # Encrypt this
            ddd[idx] = lesspass.enc_pass(text, lesspass.DEF_ENCPASS)

        else:
            # Default action
            ddd[idx] =  text

        # Pull  it back from storage
        self.model[path] = self.rec_to_tree(ddd)

        # Edited, save it
        self.save_row(ddd)

    def  onexit(self, arg, srg2 = None):
        #print("exit")
        self.exit_all()

    def exit_all(self):
        if gl_try > MAX_TRY:
            print("Extra sleep on too many tries")
            time.sleep(1)
        Gtk.main_quit()

    def load_data(self):

        ''' Load samples. Set ini flag if no passes are present.
            Create some data if none present. '''

        inited = True
        kkk = self.sql.getunikeys()
        #print("keys", kkk)
        if not kkk:
            fake = []
            if self.pgdebug > 1:
                print(" Create Init data")

            # Fill in sensible defaults (avoid blank sheet effect)
            serial = "0"; xlen = str(DEF_LEN)
            for uid, host, login in initial:
                if not uid:
                    uid = str(uuid.uuid1())
                fake.append((host, login,  serial, passx, passx,
                                xlen, "Notes Here", passx, uid))
            # Save it to fake buffer
            for aa in fake:
                #print("writing", aa[8], aa)
                ddd = self.pb.encode_data("", aa)
                self.sql.putuni(aa[8], ddd)
            kkk = self.sql.getunikeys()

        # (Re) read data
        for bb in kkk:
            #print(bb[0])
            ppp = self.sql.getuni(bb[0])
            #print("ppp", ppp)
            try:
                ddd = self.pb.decode_data(ppp[0])[0]
            except:
                print("Cannot decode", ppp);
                ddd = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                #continue

            if self.pgdebug > 3:
                print("ddd:", ddd)

            if ddd[7] != passx:
                inited &= False
            self.alldat.append(ddd)

        global gl_cnt
        gl_cnt = len(self.alldat)
        # This is running one time, always return FALSE
        return inited

    def data_to_tree(self):

        ''' Transfer from in memory to screen '''

        if self.pgdebug > 3:
            print("data_to_tree()", len(self.alldat), "items")

        self.model.clear()
        for aa in range(len(self.alldat)):
            if self.alldat[aa][8] == MASTER_TEMPLATE:
                continue

            bb = [*self.alldat[aa]]
            bb = self.rec_to_tree(bb)
            #print("data_to_tree():",  bb, "\n")
            self.model.append(None, bb)

    def rec_to_tree(self, cc):

        # Start with copy
        bb = cc[:]
        # Do not show sensitive data if not master logged in
        if self.master != FLAG_ON:
            bb[3] = passx
            bb[4] = passx
        else:
            ppp, hhh = lesspass.gen_pass_hash(bb, self.master_save)
            # Cut length as specified
            bb[3] = ppp[:int(bb[5])]

        #print("bb[4]:", bb[4])
        if bb[4] != "" and  bb[4] != passx:
            try:
                bb[4] = lesspass.dec_pass(bb[4], lesspass.DEF_ENCPASS)
            except:
                pass
                #print("decrypt", sys.exc_info())

        bb[7] = bb[7][:8] + " ... " + bb[7][:8]
        return bb

    def save_row(self, row):

        rrr = row[0:]           # Make it read / write
        rrr[3] = passx          # Not saving hash
        if self.pgdebug > 4:
            print("save_row", rrr)

        eee = self.pb.encode_data("", rrr)
        self.sql.putuni(rrr[8], eee)

    # --------------------------------------------------------------------
    def master_lock(self, butt = None):

        if self.pgdebug > 1:
            print("Master lock")

        if self.master != FLAG_OFF:
            self.status.set_markup_with_mnemonic("<span foreground=\"#AA0000\">" \
                        "Locked </span> Master pass.")
            self.stat_time = 4;

        self.master = FLAG_OFF
        self.input.set_text("")
        self.input2.set_text("")
        self.input.set_sensitive(True)
        self.buttA.set_label("   Unlo_ck   ")

        # Clear displayed secrets
        for row in self.model:
            row[3] = passx
            row[4] = passx

        self.tree.get_columns()[3].queue_resize()

        self.collab.override_background_color(Gtk.StateFlags.NORMAL,
                                                    Gdk.RGBA(.99, .1, .1))
        # No more editing
        for aa in self.cells:
            aa.set_property("editable", False)

        # Blank out QRs
        self.apply_qr("", "", "", "")

    # ------------------------------------------------------------------------------

    def master_unlock(self):

        if self.pgdebug > 1:
            print("master_unlock")

        # Quick unlock, if locked
        if self.master == FLAG_ON:
            self.message("\nAlready unlocked.")
            return

        flag = self.buttp.get_active()
        if flag:
            self.buttp.set_active(not flag)
            flag = self.buttp.get_active()

            self.input.set_visibility(flag)
            self.input2.set_visibility(flag)

        masterpass = self.input.get_text()
        self.input.set_text("")

        if not masterpass:
            self.message("\nCannot use empty Master Pass.")
            return

        if len(masterpass) < 6:
            self.message("\nCannot use less than 6 chars.")
            #self.input.set_text("")
            #self.input2.set_text("")
            return

        self.master_save =  lesspass.enc_pass(masterpass, lesspass.DEF_ENCPASS)
        masterpass = ""
        success = False
        flag = False

        for aa in self.alldat:
            drow = [*aa]
            # Not generated, do it
            if len(drow[7]) <= len(passx):
                ppp, hhh = lesspass.gen_pass_hash(drow, self.master_save)
                drow[7] = hhh
                #drow[3] = lesspass.gen_pass(strx)
                self.save_row(drow)
                flag = True

        # Re - read if needed
        if flag:
            self.alldat = []
            self.load_data()

        # Look at template first:
        auth = False
        for dd in range(len(self.alldat)):
            if self.alldat[dd][8] == MASTER_TEMPLATE:
                row = self.alldat[dd]
                # Compare
                ppp, hhh = lesspass.gen_pass_hash(row, self.master_save)
                if row[7] != hhh:
                    #print("Invalid checksum")
                    global gl_try
                    if gl_try >= MAX_TRY:
                        time.sleep(.3)
                        self.message("\nToo many tries. Exit program, and try again.")
                        time.sleep(.3)
                        self.input.set_text("")
                        return
                    self.message("\nInvalid Master pass.\n")
                    usleep(20)
                    self.input.set_text("")
                    self.status.set_text("Sleeping on retry ...")
                    self.stat_time = 2;
                    time.sleep(.3)
                    gl_try += 1
                    return
                else:
                    break

        # Second scan, display it
        for cc in range(len(self.alldat)):
            row = self.alldat[cc]
            # Compare
            ppp, hhh = lesspass.gen_pass_hash(row, self.master_save)
            if row[7] != hhh:
                print("Invalid checksum on", row[0])
                self.message("Invalid Master pass on\n"
                              "     '%s'     \n"
                                "Possibly: damaged data.\n" % row[0])
            # save back to local data
            #row[3] = ppp[:int(row[5])]
            #print("row[3]:", row[3])

            for aaa in range(len(self.cells)):
                if editable[aaa]:
                    self.cells[aaa].set_property("editable", True)
            success = True

        if success:
            self.master = FLAG_ON

            self.buttA.set_label("  Lock _Session  ")
            #print("unlocking", row[0:])
            self.row_activate(None)
            self.labn.set_markup_with_mnemonic(" Maste_r Pass:")
            self.input.set_text(""); self.input.set_sensitive(False)
            self.input2.set_text("")
            self.input2.hide(); self.labconf.hide()
            self.tree.grab_focus()

            self.status.set_markup_with_mnemonic(" <span foreground=\"#00AA00\">Unlocked. </span>" \
                        "You may now edit entries in line.")
            self.stat_time = 6
            self.collab.override_background_color(Gtk.StateFlags.NORMAL,
                                                    Gdk.RGBA(.1, .99, .1))
            # Copy data to display
            self.data_to_tree()
        else:
            self.status.set_text("Unlock failed.")
            self.stat_time = 6

    def key_press_event(self, win, event):
        #print( "key_press_event", win, event)
        self.autolog = 0
        pass

    def button_press_event(self, win, event):
        #print( "button_press_event", win, event)
        self.autolog = 0
        pass

    def message(self, strx):
        ddd = Gtk.MessageDialog()
        ddd.set_markup(strx)
        ddd.add_button("OK", Gtk.ResponseType.OK)
        #ddd.add_button("Cancel", Gtk.ResponseType.CANCEL)
        ret = ddd.run()
        #print ("ret", ret)
        ddd.destroy()

    def master_new(self, action):

        if self.pgdebug > 0:
            print("master new pressed")

        if self.ini:
            if self.input.get_text() != self.input2.get_text():
                self.message("\nThe two passes must be equal.")
                return

        if self.master == FLAG_ON:
            self.master_lock()
        else:
            self.master_unlock()

    def activate_action(self, action):

        #dialog = Gtk.MessageDialog(None, Gtk.DIALOG_DESTROY_WITH_PARENT,
        #    Gtk.MESSAGE_INFO, Gtk.BUTTONS_CLOSE,
        #    'Action: "%s" of type "%s"' % (action.get_name(), type(action)))
        # Close dialog on user response
        #dialog.connect ("response", lambda d, r: d.destroy())
        #dialog.show()
        warnings.simplefilter("ignore")
        strx = action.get_name()
        warnings.simplefilter("default")
        print ("activate_action", strx)

    def activate_quit(self, action):
        print( "activate_quit called")
        self.onexit(False)

    def activate_exit(self, action):
        print( "activate_exit called" )
        self.onexit(False)

    def activate_about(self, action):
        print( "activate_about called")
        pass

    def stat_timer(self):
        #print("Timer fired")
        if self.stat_time:
            self.stat_time -= 1
            if self.stat_time <= 0:
                self.status.set_text("Idle")
        return True

    def autologout(self):
        #print("Autologout", self.autolog)
        if self.master == FLAG_ON:
            self.autolog += 1
            if self.autolog > 5:
                self.master_lock()
            if self.autolog == 5:
                self.status.set_text("AutoLogout soon, press any key to stop it.")
                self.stat_time = 6;

        return True

    def nextfield(self, treeview, path, next_column):

        #print("nextfield()", path, next_column)
        try:
            #ret = treeview.set_cursor(path, next_column, True)
            ret = treeview.set_cursor_on_cell(path, next_column, None, True)
            #print("ret:", ret)
            usleep(50)
            #ret2 = treeview.scroll_to_cell(path, next_column, False, 0.5, 0.5)
            #print("ret2:", ret2)
        except:
            pass

    def onTreeNavigateKeyPress(self, treeview, event):
        keyname = Gdk.keyval_name(event.keyval)
        path, col = treeview.get_cursor()
        columns = [c for c in treeview.get_columns()]
        colnum = columns.index(col)
        #print("colnum", colnum, "columns", columns)
        #print("event", event.state, keyname)

        if keyname == 'Tab': # or keyname == 'Shift_L':
            # Walk to next editable
            newcol = colnum + 1
            while True:
                if newcol < len(columns):
                    next_column = columns[newcol]
                    ed = self.cells[newcol].get_property("editable")
                    if ed:
                        #print("ed", ed)
                        break
                else:
                    next_column = columns[0]
                    break
                newcol += 1

            GLib.timeout_add(50, self.nextfield, treeview, path, next_column)

        elif keyname == 'Return':

            model = treeview.get_model()
            #Check if currently in last row of Treeview
            if path.get_indices()[0] + 1 == len(model):
                path = treeview.get_path_at_pos(0,0)[0]
                #treeview.set_cursor(path, columns[colnum], True)
                GLib.timeout_add(50,
                             treeview.set_cursor,
                             path, columns[colnum], True)
            else:
                path.next()
                #treeview.set_cursor(path, columns[colnum], True)
                GLib.timeout_add(50,
                             treeview.set_cursor,
                             path, columns[colnum], True)
        else:
            pass

# Start of program:

if __name__ == '__main__':

    print("This module was not meant to be run as main.")

# EOF