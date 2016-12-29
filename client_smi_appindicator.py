#!/usr/bin/env python
from __future__ import division

import os
import signal
import json
import threading

from urllib2 import Request, urlopen, URLError

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GLib, Gtk, GObject

import socket
import json
import sys
import cairo
import os
import time

home = os.path.expanduser("~")
config_folder = os.path.join(home,'.client_smi')
if not os.path.exists(config_folder):
    os.makedirs(config_folder)
file_path = os.path.join(config_folder,'hosts_to_smi.json')
if(os.path.exists(file_path)):
    with open(file_path) as f:
        hosts = json.load(f)
else:
    with open('/usr/local/data/hosts_to_smi.json') as f:
        hosts = json.load(f)
    with open(file_path,'w') as f:
        json.dump(hosts,f)   

machines = []

for h in hosts.keys():
    try:
        machine = {}
        machine['ip'] = hosts[h]['ip']
        machine['colors'] = hosts[h]['colors']
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((machine['ip'], 1111))
        s.send("smi")

        r = s.recv(9999999)
        a = json.loads(r)

        machine['socket'] = s
        machine['name'] = h
        machine['nGPUs'] = len(a['attached_gpus'])
        machine['GPUs'] = []
        for i in range(machine['nGPUs']):
            gpu_info = a['attached_gpus'][i]
            gpu = {}
            machine['GPUs'].append(gpu)
            gpu['host'] = h+'@'+machine['ip']
            gpu['name'] = gpu_info['product_name']
            if machine['nGPUs'] > 1:
                gpu['id'] = machine['name']+':'+str(i)
            else:
                gpu['id'] = machine['name']
            gpu['memory'] = gpu_info['total_memory']/1024
            gpu['processes'] = {}
        machines.append(machine)

    except :
        pass

def main():
    indicators = {}
    for m in machines:

        for i in range(m['nGPUs']):
            gpu = m['GPUs'][i]
            indicator_id = gpu['id']
            indicator = appindicator.Indicator.new('smi_'+indicator_id, os.path.abspath('/usr/local/data/empty.png'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
            gpu['indicator'] = indicator
            indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
            build_menu(gpu)
            indicator.set_menu(gpu['menu'])
            indicator.set_label(indicator_id,'')

    notify.init('notifier')



    def smi():
        while True:
            for m in machines:
                s = m['socket']
                s.send("smi")

                r = s.recv(9999999)
                try:
                    a = json.loads(r)
                    if 'attached_gpus' in a.keys():
                        for i in range(m['nGPUs']):
                            gpu_info = a['attached_gpus'][i]
                            gpu = m['GPUs'][i]
                            gpu['utilization'] = gpu_info['utilization']['gpu']
                            gpu['used_mem'] = gpu_info['used_memory']/1024
                            update_menu(gpu)
                            icon = draw_icon(gpu,m['colors'][0],m['colors'][1],gpu['utilization']/100,gpu['used_mem']/gpu['memory'])
                            gpu['indicator'].set_icon(os.path.abspath(icon))
                            update_processes_list(gpu,gpu['processes'],gpu_info['processes'])
                except:
                    pass
 
    thread = threading.Thread(target=smi)
    thread.daemon = True
    thread.start()

    gtk.main()

def update_processes_list(gpu,old,new):
    MIN_MEM = 200
    print(old)
    print(new)
    for p in new.keys():
        if (p not in old.keys()) and new[p]['used_memory'] > MIN_MEM:
            new_job(gpu,new[p])
            print('new:\t'+new[p])
    for p in old.keys():
        if (p not in new.keys()) and old[p]['used_memory'] > MIN_MEM:
            finished_job(gpu,old[p])
            print('finished:\t'+old[p])
    gpu['processes'] = new

def update_menu(gpu):
    gpu['status'].set_label(str(gpu['utilization']) + '% , ' + '%.2f' % (gpu['used_mem']) + ' GB')
    gpu['menu'].show_all()


def build_menu(gpu):
    menu = gtk.Menu()
    host_item = gtk.MenuItem(gpu['host'])
    title_item = gtk.MenuItem(gpu['name'] + ', ' + '%.2f' % (gpu['memory']) + ' GB')
    title_item.set_sensitive(False)
    gpu['status'] = gtk.MenuItem('')
    menu.append(host_item)
    menu.append(title_item)
    menu.append(gpu['status'])
    menu.show_all()
    gpu['menu'] = menu

def draw_icon(gpu,color1,color2,percentage1,percentage2):
    '''Draws a graph with 2 columns 1 for each percentage (1 is fuill, 0 is empty)'''
    WIDTH, HEIGHT = 22, 22
    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context (surface)
    ctx.scale (WIDTH, HEIGHT) # Normalizing the canvas

    ctx.rectangle (0, 1-percentage1, 0.5, 1) # Rectangle(x0, y0, x1, y1)
    ctx.set_source_rgb(color1[0]/255,color1[1]/255,color1[2]/255)
    ctx.fill ()

    ctx.rectangle (0.5, 1-percentage2, 1, 1) # Rectangle(x0, y0, x1, y1)
    ctx.set_source_rgb(color2[0]/255,color2[1]/255,color2[2]/255)
    ctx.fill ()
    if 'i' not in gpu.keys():
        gpu['i'] = 0
    png_name = os.path.join(config_folder,gpu['id']+str(gpu['i'])+'.png')
    gpu['i'] = (gpu['i']+1)%2

    surface.write_to_png (png_name) # Output to PNG


    return(png_name)

def new_job(gpu,job):
    notify.Notification.new("<b>New Job for "+gpu['id']+"</b>", job['process_name'] + '\n' + '%.2f' % (job['used_memory']/1024) + ' Go usage', None).show()

def finished_job(gpu,job):
    notify.Notification.new("<b>Finished Job for "+gpu['id']+"</b>", job['process_name'] + '\n' + '%.2f' % (job['used_memory']/1024) + ' Go usage', None).show()    




if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    GObject.threads_init()
    main()
