#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk
from gi.repository import AppIndicator3
import os

class UnityTrayPlaces:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "Unity Tray Places 0.0.1",
            "preferences-system-windows",
            # "folder-open",
            # "image-x-generic",
            # "drive-multidisk",
            # "network-server",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.create_menu())
    
    def read_gtk_bookmarks(self):
        # Read GTK bookmarks file
        bookmarks_file = os.path.expanduser("~/.config/gtk-3.0/bookmarks")
        if os.path.exists(bookmarks_file):
            with open(bookmarks_file, 'r') as f:
                return f.read().splitlines()
        return []
    
    def create_menu(self):
        menu = Gtk.Menu()
        # Add GTK bookmarks
        bookmarks = self.read_gtk_bookmarks()
        for bookmark in bookmarks:
            label = bookmark.split(' ')[-1]
            path = bookmark.split(' ')[0]
            item = Gtk.MenuItem(label=label)
            item.connect("activate", self.open_bookmark, path)
            menu.append(item)
        # Add separator
        menu.append(Gtk.SeparatorMenuItem())
        # Add quit item
        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)
        menu.show_all()
        return menu
    
    def open_bookmark(self, widget, path):
        # open default file manager
        try:
            exit_code = os.system(f"xdg-open '{path}'")
            if exit_code != 0:
                raise Exception(f"Failed to open '{path}'")
        except Exception as e:
            os.system(f"notify-send '{str(e)}'")
            # dialog = Gtk.MessageDialog(
                # parent=None,
                # flags=0,
                # message_type=Gtk.MessageType.ERROR,
                # buttons=Gtk.ButtonsType.OK,
                # text=f"{str(e)}"
            # )
            # dialog.run()
            # dialog.destroy()
    
    def quit(self, widget):
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Are you sure?"
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            Gtk.main_quit()

if __name__ == "__main__":
    UnityTrayPlaces()
    Gtk.main()
