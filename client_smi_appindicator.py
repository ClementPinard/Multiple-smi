#!/usr/bin/env python
from __future__ import division

import os
import signal
import json
import threading
import cairo
import time
import client_smi

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GObject
from gi.repository import GLib

client_smi.parser.add_argument('--min-mem-notif', '-n', default=200, help='min memory usage to trigger Notification')
config_folder = client_smi.config_folder
hosts = client_smi.hosts


def main():
    args = client_smi.parser.parse_args()
    for name, machine in hosts.items():
        if 'index' in machine.keys():
            index = str(machine['index'])
        else:
            index = '0'
        indicator = appindicator.Indicator.new(
            's'+index+'_'+name,
            os.path.abspath('/usr/local/data/empty.png'),
            appindicator.IndicatorCategory.SYSTEM_SERVICES)
        machine['indicator'] = indicator
        machine['indicator'].set_label(name,'')
    notify.init('notifier')

    def smi():
        ticks = 0
        online_machines = []
        while True:
            if ticks == 0:
                new_machines, online_machines = client_smi.update_online_machines(args, hosts, online_machines)
                GLib.idle_add(notify_new_machines, new_machines, hosts)
            ticks = (ticks + 1) % args.refresh_rate
            time.sleep(1)
            for name, machine in hosts.items():
                if name in online_machines:
                    s = machine['socket']
                    try:
                        s.send(b'smi')
                        r = s.recv(args.max_size).decode('utf-8')
                        a = json.loads(r)
                    except Exception as e:
                        GLib.idle_add(lost_machine, name, hosts[name])
                        online_machines.remove(name)
                    else:
                        if 'attached_gpus' in a.keys():
                            for i in range(machine['nGPUs']):
                                gpu_info = a['attached_gpus'][0]
                                gpu = machine['GPUs'][i]
                                gpu['utilization'] = gpu_info['utilization']['gpu']
                                gpu['used_mem'] = gpu_info['used_memory']/1024
                                update_processes_list(name, gpu, gpu_info['processes'], args.min_mem_notif)
                        GLib.idle_add(update_menu, machine)
                        icon = draw_icon(name, machine)
                        GLib.idle_add(machine['indicator'].set_icon, os.path.abspath(icon))

    thread = threading.Thread(target=smi)
    thread.daemon = True
    thread.start()
    gtk.main()


def update_processes_list(machine_name, gpu, new, mem_threshold):
    old = gpu['processes']
    for p in new.keys():
        if p not in old.keys() and new[p]['used_memory'] > mem_threshold:
            new_job(machine_name,gpu,new[p])
            print('new: ({})\t{}'.format(gpu['id'],new[p]))
            gpu['processes'][p] = new[p]
        elif p in old.keys():
            gpu['processes'][p] = new[p]
    for p in list(old.keys()):
        if p not in new.keys() and old[p]['used_memory'] > mem_threshold:
            finished_job(machine_name,gpu,old[p])
            print('finished: ({})\t{}'.format(gpu['id'], old[p]))
            gpu['processes'].pop(p,None)


def update_menu(machine):
    for gpu in machine['GPUs']:
        time.sleep(0.1)
        gpu['status'].set_label("{}% , {:,.2f} GB".format(gpu['utilization'], gpu['used_mem']))
    machine['menu'].show_all()


def build_menu(machine_name, machine):
    menu = gtk.Menu()
    host_item = gtk.MenuItem("{}@{}".format(machine_name, machine['ip']))
    menu.append(host_item)
    for gpu in machine['GPUs']:
        gpu['title'] = gtk.MenuItem("{}, {:.2f} GB".format(gpu['name'], gpu['memory']))
        gpu['title'].set_sensitive(False)
        gpu['status'] = gtk.MenuItem("{}% , {:.2f} GB".format(gpu['utilization'], gpu['used_mem']))
        menu.append(gpu['title'])
        menu.append(gpu['status'])
    menu.show_all()
    return menu


def draw_icon(machine_name, machine):
    '''Draws a graph with 2 columns 1 for each percentage (1 is full, 0 is empty)'''
    color1, color2 = machine['colors']
    WIDTH, HEIGHT = 22, 22
    if machine['nGPUs'] > 2:
        WIDTH = 11*machine['nGPUs']  # if more than 1 GPU on a machine, each column is 11px wide (and not 22px)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    ctx.scale(WIDTH/machine['nGPUs'], HEIGHT)  # Normalizing the canvas coordinates go from (0,0) to (nGPUs,1)

    for i in range(machine['nGPUs']):
        gpu = machine['GPUs'][i]
        percentage1,percentage2 = gpu['utilization']/100,gpu['used_mem']/gpu['memory']
        ctx.rectangle(i, 1-percentage1, 0.5, percentage1)  # Rectangle(x0, y0, x1, y1)
        ctx.set_source_rgb(color1[0]/255,color1[1]/255,color1[2]/255)
        ctx.fill()

        ctx.rectangle(i+0.5, 1-percentage2, 0.5, percentage2)  # Rectangle(x0, y0, x1, y1)
        ctx.set_source_rgb(color2[0]/255,color2[1]/255,color2[2]/255)
        ctx.fill()
    if 'i' not in machine.keys():
        machine['i'] = 0
    png_name = os.path.join(config_folder,"{}{}.png".format(machine_name, machine['i']))
    machine['i'] = (machine['i']+1) % 2

    surface.write_to_png(png_name)  # Output to PNG
    return(png_name)


def new_job(machine_name, gpu, job):
    notify.Notification.new(
        "New Job for {}".format(machine_name),
        "{}\n{}\n{:.2f} Go usage".format(gpu['id'],job['process_name'],job['used_memory']/1024),
        None).show()
    return


def finished_job(machine_name, gpu, job):
    notify.Notification.new(
        "Finished Job for {}".format(machine_name),
        "{}\n{}\n{:.2f} Go usage".format(gpu['id'],job['process_name'],job['used_memory']/1024),
        None).show()
    return


def notify_new_machines(machine_names, hosts):
    for name in machine_names:
        machine = hosts[name]
        machine['indicator'].set_status(appindicator.IndicatorStatus.ACTIVE)
        machine['menu'] = build_menu(name, machine)
        machine['indicator'].set_menu(machine['menu'])

    if len(machine_names) == 1:
        notify.Notification.new(
            "{} Connected".format(machine_names[0]),
            hosts[machine_names[0]]['ip'],
            None).show()
    elif len(machine_names) > 1:
        notify.Notification.new(
            "New machines connected",
            '\n'.join(['{}\t({})'.format(name, hosts[name]['ip']) for name in machine_names]),
            None).show()
    return


def lost_machine(machine_name, machine):
    machine['indicator'].set_status(appindicator.IndicatorStatus.PASSIVE)
    notify.Notification.new(
        "{} Disconnected".format(machine_name),
        machine['ip'],
        None).show()
    return


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    GObject.threads_init()
    main()
