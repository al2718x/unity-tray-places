#!/usr/bin/env python3

from configparser import ConfigParser
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk
from gi.repository import AppIndicator3
import os
import xml.etree.ElementTree as ET
import urllib.parse

class UnityTrayPlaces:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "Unity Tray Places 0.0.5",
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

    def read_recently_used(self):
        # Read recently used files
        recently_used_file = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(recently_used_file):
            with open(recently_used_file, 'r') as f:
                return f.read()
        return ""

    def parse_recently_used(self) -> dict:
        # xml structure:
        # <xbel>
        #   <bookmark href="file:///home/user/Documents" modified="2025-10-14T12:34:56">
        #     {{omit this}}
        #     <info>
        #       {{omit this}}
        #     </info>
        #   </bookmark>
        # </xbel>
        xml = self.read_recently_used()
        tree = ET.fromstring(xml)
        bookmarks = {}
        for bookmark in tree.findall('bookmark'):
            href = bookmark.get('href')
            if not href:
                continue
            # if prefix is not file://, skip
            if not href.startswith('file://'): # mtp://, sftp://, trash://, etc.
                continue
            # skip prefix, decode URL-encoded characters
            path = urllib.parse.unquote(href.replace('file://', ''))
            bookmarks[path] = {
                'href': href,
                # get first 20 and last 100 chars if length > 120
                'path_cropped': path if len(path) <= 120 else path[:20] + ' ... ' + path[-100:],
                'file_name': os.path.basename(path),
                'modified': bookmark.get('modified'),
                'visited': bookmark.get('visited')
            }
        # sort by modified (most recent first)
        bookmarks = dict(sorted(bookmarks.items(), key=lambda x: x[1]['modified'], reverse=True))
        # take first 20 existing files
        existing_bookmarks = {}
        count = 0
        for k, v in list(bookmarks.items()):
            if os.path.exists(k):
                existing_bookmarks[k] = v
                count += 1
            if count >= 20:
                break
        return existing_bookmarks

    # class CaseConfigParser(ConfigParser):
        # def optionxform(self, optionstr):
            # return optionstr

    def read_config(self):
        # config = self.CaseConfigParser()
        config = ConfigParser()
        config.optionxform = str
        config.read(".config")
        try:
            return dict(config.items("my-places", raw=True))
        except:
            return {}

    def create_menu(self):
        menu = Gtk.Menu()

        # add custom places from .config
        custom_places = self.read_config()
        for name, path in custom_places.items():
            item = Gtk.MenuItem(label=name)
            item.connect("activate", self.open_bookmark, path)
            menu.append(item)

        # add GTK bookmarks
        bookmarks = self.read_gtk_bookmarks()
        for bookmark in bookmarks:
            label = bookmark.split(' ')[-1]
            path = bookmark.split(' ')[0]
            item = Gtk.MenuItem(label=label)
            item.connect("activate", self.open_bookmark, path)
            menu.append(item)

        # add separator
        menu.append(Gtk.SeparatorMenuItem())

        # add submmenu for recently used files
        recently_used_menu = Gtk.Menu()
        # Initial load of recently used files
        self.reload_recently_used_menu(None, recently_used_menu)
        recently_used_item = Gtk.MenuItem(label="Recently Used")
        recently_used_item.set_submenu(recently_used_menu)
        # connect to "activate" signal to reload recently used files each time menu is opened
        recently_used_item.connect("activate", self.reload_recently_used_menu, recently_used_menu)
        menu.append(recently_used_item)

        # add separator
        menu.append(Gtk.SeparatorMenuItem())

        # add restart item
        item_restart = Gtk.MenuItem(label="Restart")
        item_restart.connect("activate", self.restart)
        menu.append(item_restart)

        # add quit item
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

    def reload_recently_used_menu(self, widget, submenu):
        # Clear existing menu items
        for item in submenu.get_children():
            submenu.remove(item)
        # Reload recently used files
        recently_used = self.parse_recently_used()
        for path, data in recently_used.items():
            # Create a box to hold label and use it for better tooltip support
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=data['path_cropped'])
            box.pack_start(label, True, True, 0)
            item = Gtk.MenuItem()
            item.add(box)
            item.set_tooltip_text(path)  # add tooltip showing full file path
            item.connect("activate", self.open_bookmark, path)
            submenu.append(item)
        submenu.show_all()

    def restart(self, widget):
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
            os.system("./run &")
            Gtk.main_quit()

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
    # parser = UnityTrayPlaces()
    # bookmarks = parser.parse_recently_used()
    # for path, bookmark in bookmarks.items():
        # print('-' * 50)
        # print(f"Path: {path}")
        # print(f"Href: {bookmark['href']}")
        # print(f"Path cropped: {bookmark['path_cropped']}")
        # print(f"File: {bookmark['file_name']}")
        # print(f"Modified: {bookmark['modified']}")
        # print(f"Visited: {bookmark['visited']}")
    # print('=' * 50)
    # print(f'total: {len(bookmarks)}')

    UnityTrayPlaces()
    Gtk.main()
