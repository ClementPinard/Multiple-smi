import os
import signal
import threading
import time

import gi

from .default_frontend import BaseFrontend
from .icon_utils import draw_icon

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3 as appindicator  # noqa
from gi.repository import GLib, GObject  # noqa
from gi.repository import Gtk as gtk  # noqa


def build_menu_gtk(machine_name, summary):
    menu = gtk.Menu()
    host_item = gtk.MenuItem(f"{machine_name}@{summary['ip']}")
    menu.append(host_item)

    for gpu in summary["GPUs"]:
        gpu["title"] = gtk.MenuItem(f"{gpu['name']}, {gpu['memory']:.2f} GB")
        gpu["title"].set_sensitive(False)
        gpu["status"] = gtk.MenuItem(
            f"{gpu['utilization']}% , {gpu['used_mem']:.2f} GB"
        )
        menu.append(gpu["title"])
        menu.append(gpu["status"])
    cpu_title = gtk.MenuItem(summary["cpu"]["name"])
    cpu_title.set_sensitive(False)
    summary["cpu_usage_menu"] = gtk.MenuItem(f"{summary['cpu']['usage']}%")
    menu.append(cpu_title)
    menu.append(summary["cpu_usage_menu"])
    ram_title = gtk.MenuItem("RAM")
    ram_title.set_sensitive(False)
    menu.append(ram_title)

    summary["ram_usage_menu"] = gtk.MenuItem(
        "{}% ({:.2f} GB / {:.2f} GB)".format(
            summary["ram"]["usage"], summary["ram"]["used"], summary["ram"]["total"]
        )
    )
    menu.append(summary["ram_usage_menu"])
    menu.show_all()
    return menu


def update_menu_gtk(machine_name, summary):
    if "indicator" not in summary.keys():
        return
    if "menu" not in summary.keys():
        summary["menu"] = build_menu_gtk(machine_name, summary)
        summary["indicator"].set_menu(summary["menu"])
    for gpu in summary["GPUs"]:
        time.sleep(0.1)
        gpu["status"].set_label(f"{gpu['utilization']}% , {gpu['used_mem']:,.2f} GB")
    summary["cpu_usage_menu"].set_label(f"{summary['cpu']['usage']}%")
    summary["ram_usage_menu"].set_label(
        "{}% ({:.2f} GB / {:.2f} GB)".format(
            summary["ram"]["usage"], summary["ram"]["used"], summary["ram"]["total"]
        )
    )
    summary["menu"].show_all()


class AppIdFrontend(BaseFrontend):
    def __init__(self, config_folder):
        super().__init__(config_folder)
        GObject.threads_init()

    def launch(self, func, *args, **kwargs):
        kwargs["frontend"] = self
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        gtk.main()
        return

    def update_menu(self, machine_name, machine):
        summary = machine["summary"]
        GLib.idle_add(update_menu_gtk, machine_name, summary)
        icon = draw_icon(machine)
        if "i" not in machine.keys():
            machine["i"] = 0
        png_name = os.path.join(self.config_folder, f"{machine_name}{machine['i']}.png")
        machine["i"] = (machine["i"] + 1) % 2

        icon.write_to_png(png_name)
        GLib.idle_add(summary["indicator"].set_icon, os.path.abspath(png_name))

    def new_machines(self, machine_names, machines):
        for name in machine_names:
            machine = machines[name]
            summary = machine["summary"]
            if "index" in machine.keys():
                index = str(machine["index"])
            else:
                index = "0"
            indicator = appindicator.Indicator.new(
                "s" + index + "_" + name,
                os.path.join("data", "empty.png"),
                appindicator.IndicatorCategory.SYSTEM_SERVICES,
            )
            summary["indicator"] = indicator
            summary["indicator"].set_label(name, "")
            summary["indicator"].set_status(appindicator.IndicatorStatus.ACTIVE)

    def lost_machine(self, machine_name, machine):
        machine["summary"]["indicator"].set_status(appindicator.IndicatorStatus.PASSIVE)
        del machine["summary"]["indicator"]
        del machine["summary"]["menu"]
