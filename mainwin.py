#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function

import os, sys, getopt, signal, random, time, warnings, string
import qrcode, uuid

from PIL import Image, ImageFilter, ImageOps

#import Crypto.Hash
#print(dir(Crypto.Hash.__doc__))
#print(Crypto.Hash.__doc__)

from Crypto.Hash import MD2

import  lesspass

from pymenu import  *

sys.path.append('../pycommon')

import  pypacker
from    pgutil import  *
from    pgui import  *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Pango

DEF_LEN = 14            # Default pass len
MAX_TRY = 4

# Fields become editable
fields = ("Site", "Login", "Serial", "Pass", "Override",
            "Len", "Notes",  "ChkSum", "UUID",  )

passx   = " - " * 10
gl_try  = 0

# ------------------------------------------------------------------------

class MainWin(Gtk.Window):

    def __init__(self, sql):

        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.sql = sql
        self.master = False
        self.pb  = pypacker.packbin()
        self.darr = []

        #self = Gtk.Window(Gtk.WindowType.TOPLEVEL)

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
            self.set_default_size(7*hhh/8, 4*hhh/8)
        else:
            self.set_default_size(4*www/8, 4*hhh/8)

        self.connect("destroy", self.OnExit)
        self.connect("key-press-event", self.key_press_event)
        self.connect("button-press-event", self.button_press_event)

        try:
            self.set_icon_from_file("icon.png")
        except:
            pass

        vbox = Gtk.VBox(); hbox4 = Gtk.HBox(); hbox5 = Gtk.HBox()

        merge = Gtk.UIManager()
        #self.mywin.set_data("ui-manager", merge)

        aa = create_action_group(self)
        merge.insert_action_group(aa, 0)
        self.add_accel_group(merge.get_accel_group())

        merge_id = merge.new_merge_id()

        try:
            mergeid = merge.add_ui_from_string(ui_info)
        except GLib.GError as msg:
            print("Building menus failed: %s" % msg)

        self.mbar = merge.get_widget("/MenuBar")
        self.mbar.show()

        self.tbar = merge.get_widget("/ToolBar");
        self.tbar.show()

        bbox = Gtk.VBox()
        bbox.pack_start(self.mbar, 0,0, 0)
        bbox.pack_start(self.tbar, 0,0, 0)
        vbox.pack_start(bbox, False, 0, 0)

        hbox4.pack_start(Gtk.Label("  "), 0, 0, 4)

        self.labn = Gtk.Label.new_with_mnemonic("  Ma_ster Pass:")

        hbox4.pack_start(self.labn, 0, 0, 4)
        self.input = Gtk.Entry()
        self.input.connect("activate", self.activate)
        self.input.set_visibility(False)
        self.labn.set_mnemonic_widget(self.input)

        hbox4.pack_start(self.input, 0, 0, 4)

        buttA = Gtk.Button.new_with_mnemonic("   Unlo_ck   ")
        buttA.connect("clicked", self.master_new)
        hbox4.pack_start(buttA, False, 0, 2)

        lab2 = Gtk.Label("  Status:   ");  hbox4.pack_start(lab2, 0, 0, 0)
        self.status = Gtk.Label("Idle.");
        self.status.set_xalign(0)
        hbox4.pack_start(self.status, 1, 1, 0)

        buttB = Gtk.Button.new_with_mnemonic("   Lock _Data  ")
        buttB.connect("clicked", self.master_lock)
        hbox4.pack_start(buttB, False, 0, 2)

        hbox4.pack_start(Gtk.Label(" "), 0, 0, 0)

        butt2 = Gtk.Button.new_with_mnemonic("    E_xit    ")
        butt2.connect("clicked", self.OnExit, self)
        hbox4.pack_start(butt2, False, 0, 0)

        lab2 = Gtk.Label("  ");  hbox4.pack_start(lab2, 0, 0, 0)

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
        laba2 = Gtk.Label("Auth"); laba2.set_tooltip_text("QR code for selected password")
        self.pad.append_page(self.edit2, laba2)
        laba3 = Gtk.Label("Over"); laba3.set_tooltip_text("QR code for selected override")
        self.pad.append_page(self.edit3, laba3)

        tt = type(""); fff = []
        for ccc in range(len(fields)):
            fff.append(tt)
        self.model = Gtk.TreeStore(*fff)
        self.tree = Gtk.TreeView(self.model)
        self.tree.connect("cursor-changed", self.row_activate)

        self.cells = []; cntf = 0
        for aa in fields:
            col = Gtk.TreeViewColumn(aa, self.cellx(cntf), text=cntf)
            self.tree.append_column(col)
            cntf += 1

        self.hpane = Gtk.HPaned()
        self.hpane.set_position(300)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.add_with_viewport(self.tree)

        ret = self.fill_samples()
        if not ret:
            self.labn.set_markup_with_mnemonic(" <span foreground=\"#880000\"> !!! New !!!</span> Ma_ster Pass:")

        #vbox3 = Gtk.VBox()
        #vbox3.pack_start(self.scroll, 1, 1, 0)

        hbox6 = Gtk.HBox()
        hbox6.pack_start(Gtk.Label(" "), 0, 0, 2)
        butt1 = Gtk.Button.new_with_mnemonic("   _New Row  ")
        butt1.connect("clicked", self.add_newrow)
        hbox6.pack_start(butt1, 0, 0, 2)
        butt2 = Gtk.Button.new_with_mnemonic("   Del Row  ")
        butt2.connect("clicked", self.del_row)
        hbox6.pack_start(butt2, 0, 0, 2)

        hbox6.pack_start(Gtk.Label("   "), 0, 0, 2)
        butt1 = Gtk.Button.new_with_mnemonic("   Copy Lo_gin  ")
        butt1.connect("clicked", self.copy)
        hbox6.pack_start(butt1, 0, 0, 2)
        butt2 = Gtk.Button.new_with_mnemonic("   Copy Au_th  ")
        butt2.connect("clicked", self.copy2)
        hbox6.pack_start(butt2, 0, 0, 2)
        butt2a = Gtk.Button.new_with_mnemonic("   Copy Override  ")
        butt2a.connect("clicked", self.copy3)
        hbox6.pack_start(butt2a, 0, 0, 2)

        hbox6.pack_start(Gtk.Label(" "), 1, 1, 2)

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

        self.input.grab_focus_without_selecting()

        self.stat_time = 0
        GLib.timeout_add(1000, self.timer)


    def activate(self, arg1):
        #print("activate")
        self.master_unlock()

    def copy(self, arg):
        print("Called copy")
        if not self.master:
            self.message("Cannot copy record if master key is not entered")
            return
        self.status.set_text("Copied login")
        self.stat_time = 0;

    def copy2(self, arg):
        print("Called copy2")
        if not self.master:
            self.message("Cannot copy auth record if master key is not entered")
            return

    def copy3(self, arg):
        print("Called copy3")
        if not self.master:
            self.message("Cannot copy override record if master key is not entered")
            return

    def row_activate(self, arg1):
        sel = self.tree.get_selection()
        tree, curr = sel.get_selected()
        if not curr:
            return

        #print("row_activate",  curr)
        ppp = self.model.get_path(curr)
        row = self.model[ppp]
        self.apply_qr(row[1], row[3], row[4], row[0])

    def del_row(self, arg1):

        if not self.master:
            self.message("Cannot delete record if master key is not entered")
            return

        sel = self.tree.get_selection()
        tree, curr = sel.get_selected()
        if not curr:
            self.message("Plase select a row to delete")
            return


    def add_newrow(self, arg1):

        if not self.master:
            self.message("Cannot add record if master key is not entered")
            return

        #(random.random() * 100)
        xlen = len(self.model)
        self.model.append(None,
                ("host_%d" % xlen, "login",  "0", passx, passx, str(DEF_LEN),
                    "Notes Here", "Chksum", str(uuid.uuid4()),)
              )

        sel = self.tree.get_selection()
        iter = self.model.get_iter_first()
        while True:
            iter2 =  self.model.iter_next(iter)
            if not iter2:
                break
            iter = iter2
        sel.select_iter(iter)

    def apply_qr(self, strx, passx, over, site):
        #print ("new QR", strx)
        qq =  qrcode.make(strx, version=1)
        dd = self.image2pixbuf(qq)
        self.edit.set_from_pixbuf(dd)
        qq =  qrcode.make(passx, version=1)
        dd = self.image2pixbuf(qq)
        self.edit2.set_from_pixbuf(dd)
        qq =  qrcode.make(over, version=1)
        dd = self.image2pixbuf(qq)
        self.edit3.set_from_pixbuf(dd)
        qq =  qrcode.make(site, version=1)
        dd = self.image2pixbuf(qq)
        self.edit4.set_from_pixbuf(dd)

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
        #cell.set_property("editable", True)
        cell.connect("edited", self.text_edited, idx)
        self.cells.append(cell)
        return cell

    def text_edited(self, widget, path, text, idx):

        if not self.master:
            self.message("Cannot edit if master key is not entered")
            return

        # Changed?
        if  self.model[path][idx] != text:
            #print("modified", path, self.model[path][idx], text)
            row = self.model[path]
            if idx == 0 or idx == 1:
                self.model[path][idx] = str(text)
                # Re-generate this one
                master = self.input.get_text()
                strx = lesspass.gen_pass(row[0] + row[1] + master + str(int(row[2])))
                #print("strx", strx)
                row[3] = strx[:int(row[5])]
                hh = MD2.new(); hh.update(strx.encode()); sss = hh.hexdigest()
                row[7] = sss
            elif idx == 2:
                try:
                    self.model[path][idx] = str(int(text))
                except:
                    self.message("\nSerial field must be an integer")
                # Re-generate this one
                master = self.input.get_text()
                strx = lesspass.gen_pass(row[0] + row[1] + master + str(int(row[2])))
                #print("strx", strx)
                row[3] = strx[:int(row[5])]
                hh = MD2.new(); hh.update(strx.encode()); sss = hh.hexdigest()
                row[7] = sss

            elif idx == 5:
                try:
                    self.model[path][idx] = str(int(text))
                except:
                    self.message("\nLength field must be an integer")

                if int(self.model[path][idx]) > 24:
                    self.model[path][idx] = "24"
                    self.message("\nLength field must be 32 or less")
            else:
                self.model[path][idx] = text

            #self.master_unlock()
            self.save_row(self.model[path], int(path))

    def  OnExit(self, arg, srg2 = None):
        #print("exit")
        self.exit_all()

    def exit_all(self):
        if gl_try > MAX_TRY:
            print("Extra sleep on too many tries")
            time.sleep(1)
        Gtk.main_quit()

    def fill_samples(self):
        ret = 0
        kkk = self.sql.getunikeys()
        #print("keys", kkk)
        if not kkk:
            # fill in something (so no blank seet effect)
            serial = "0"; xlen = "14"
            initial = [("host.com", "username1"), ("example.com", "username2"),
                        ("noname.com", "username3"), ]
            for host, login in initial:
                self.model.append(None, (host, login,  serial, passx, passx, xlen, "Notes", passx, str(uuid.uuid4()) ))

            # Save it
            for aa in self.model:
                #print("writing", aa[8], aa[0:])
                ddd = self.pb.encode_data("", aa[0:])
                self.sql.putuni(aa[8], ddd)
        else:
            for bb in kkk:
                #print(bb[0])
                ppp = self.sql.getuni(bb[0])
                #print("ppp", ppp)
                try:
                    ddd = self.pb.decode_data(ppp[0])[0]
                except:
                    print("Cannot decode", ppp);
                    ddd = [0, 0, 0, 0, 0, 0, 0, 0, 0]
                    continue

                #print(ddd)

                if ddd[4] != passx:
                    #self.darr.append(lesspass.dec_pass(ddd[4], self.input.get_text()))
                    self.darr.append(ddd[4])
                    ddd[4] = passx
                else:
                    self.darr.append(ddd[4])

                self.model.append(None, (ddd[0], ddd[1], ddd[2], ddd[3], ddd[4], ddd[5], ddd[6], ddd[7], ddd[8]))
                if ddd[7] !=  passx:
                    ret |=  True
        #print("darr", self.darr)
        return ret

    def save_row(self, row, cnt):
        rrr = row[0:]
        rrr[3] = passx
        if len(self.darr[cnt]) == 1:
            rrr[4] = self.darr[cnt]
        #print("save_row rrr", rrr)
        eee = self.pb.encode_data("", rrr[0:])
        self.sql.putuni(rrr[8], eee)

    # --------------------------------------------------------------------
    def master_lock(self, butt):

        if self.master:
            self.status.set_text("Locked Master pass")
            self.stat_time = 0;

        self.master = False
        self.input.set_text("")

        for row in self.model:
            row[3] = passx
            row[4] = passx
        pass
        for aa in self.cells:
            aa.set_property("editable", False)

    # ------------------------------------------------------------------------------

    def master_unlock(self):

        if self.master:
            self.message("\nAlready unlocked")
            return

        master = self.input.get_text()

        if not master:
            self.message("\nCannot use empty Master Pass")
            return
        #serial = 0;

        if len(master) < 6:
            self.message("\nCannot use less than 6 chars")
            return

        cno = 0
        for row in self.model:
            #print("data", row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
            strx = lesspass.gen_pass(row[0] + row[1] + master + str(int(row[2])))
            #print("strx", strx)
            hh = MD2.new(); hh.update(strx.encode()); sss = hh.hexdigest()
            #print("chksum", row[7], sss)
            if len(row[7]) <= len(passx):
                #print("gen", sss)
                row[7] = sss
            if len(self.darr[cno]) == 1:
                print("decode", self.darr[cno])
                row[4] = self.darr[cno][2]
            else:
                if row[7] != sss:
                    #print("Invalid checksum")
                    global gl_try
                    if gl_try > MAX_TRY:
                        self.message("Too many tries")
                        return

                    self.message("Invalid Master pass")
                    usleep(20)

                    self.status.set_text("Sleeping on retry")
                    self.stat_time = 0;
                    time.sleep(.3)
                    gl_try += 1
                    break

            self.master = True
            #print("unlocking", row[0:])
            self.model[cno] = (row[0], row[1], row[2], strx[:int(row[5])], row[4], row[5], row[6], row[7], row[8])
            self.save_row(self.model[cno], cno)

            #for aa in range(self.tree.get_n_columns()):
            #ttt = self.tree.get_column(aa)

            for aa in range(len(self.cells)):
                if aa != 3 and aa != 7 and aa != 8:
                    self.cells[aa].set_property("editable", True)

            cno += 1

        self.row_activate(None)
        self.labn.set_markup_with_mnemonic(" Ma_ster Pass:")


    def key_press_event(self, win, event):
        #print( "key_press_event", win, event)
        pass

    def button_press_event(self, win, event):
        #print( "button_press_event", win, event)
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
        #print("master pressed", self.input.get_text())
        master = self.input.get_text()
        if not master:
            self.message("\nCannot use empty Master Pass")
            return
        # Check it
        #print("Check master", master)
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
        self.OnExit(False)

    def activate_exit(self, action):
        print( "activate_exit called" )
        self.OnExit(False)

    def activate_about(self, action):
        print( "activate_about called")
        pass

    def timer(self):
        #print("Timer fired")
        self.stat_time += 1
        if self.stat_time == 3:
            self.status.set_text("Idle")

        return True

# Start of program:

if __name__ == '__main__':

    mainwin = MainWin()
    Gtk.main()

# EOF