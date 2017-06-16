#!/usr/bin/env python
from __future__ import division

import os
import signal
import json
import threading

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

MIN_MEM_NOTIF = 200
port = 26110
max_size = 10240 #10 ko
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
        if "index" in hosts[h].keys():
            machine["index"] = hosts[h]["index"]
        s = socket.create_connection((machine['ip'], port))
        s.send("smi")

        r = s.recv(max_size) #10ko max
        a = json.loads(r)

        machine['socket'] = s
        machine['name'] = h
        machine['nGPUs'] = len(a['attached_gpus'])
        machine['GPUs'] = []
        machine['host'] = h+'@'+machine['ip']

        for i in range(machine['nGPUs']):
            gpu_info = a['attached_gpus'][i]
            gpu = {}
            machine['GPUs'].append(gpu)
            gpu['name'] = gpu_info['product_name']
            if machine['nGPUs'] > 1:
                gpu['id'] = machine['name']+':'+str(i)
            else:
                gpu['id'] = machine['name']
            gpu['memory'] = gpu_info['total_memory']/1024
            gpu['processes'] = {}
            gpu['utilization'] = gpu_info['utilization']['gpu']
            gpu['used_mem'] = gpu_info['used_memory']/1024
            gpu['processes'] = gpu_info['processes']
        machines.append(machine)

    except:
        pass

def main():
    indicators = {}
    for m in machines:
        indicator_id = m['name']
        if 'index' in m.keys():
            index = str(m['index'])
        else:
            index= '0'
        indicator = appindicator.Indicator.new('s'+index+'_'+indicator_id, os.path.abspath('/usr/local/data/empty.png'), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        m['indicator'] = indicator
        indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        build_menu(m)
        indicator.set_menu(m['menu'])
        indicator.set_label(indicator_id,'')

    notify.init('notifier')



    def smi():
        while True:
            time.sleep(1)
            for m in machines:
                s = m['socket']
                try:
                    s.send("smi")
                    r = s.recv(max_size)
                    a = json.loads(r)
                    if 'attached_gpus' in a.keys():
                        for i in range(m['nGPUs']):
                            gpu_info = a['attached_gpus'][0]
                            gpu = m['GPUs'][i]
                            gpu['utilization'] = gpu_info['utilization']['gpu']
                            gpu['used_mem'] = gpu_info['used_memory']/1024
                            update_processes_list(gpu,gpu['processes'],gpu_info['processes'])
                    update_menu(m)
                    icon = draw_icon(m,m['colors'][0],m['colors'][1])
                    m['indicator'].set_icon(os.path.abspath(icon))
                except:
                    raise

    thread = threading.Thread(target=smi)
    thread.daemon = True
    thread.start()

    gtk.main()

def update_processes_list(gpu,old,new):
    for p in new.keys():
        if p not in old.keys() and new[p]['used_memory'] > MIN_MEM_NOTIF:
            new_job(gpu,new[p])
            print('new: ('+gpu['id']+')\t' + str(new[p]))
            gpu['processes'][p] = new[p]
        elif p in old.keys():
            gpu['processes'][p] = new[p]
    for p in old.keys():
        if p not in new.keys() and old[p]['used_memory'] > MIN_MEM_NOTIF:
            finished_job(gpu,old[p])
            print('finished: ('+gpu['id']+')\t'+str(old[p]))
            gpu['processes'].pop(p,None)

def update_menu(machine):
    for gpu in machine['GPUs']:
        time.sleep(0.01)
        gpu['status'].set_label(str(gpu['utilization']) + '% , ' + '%.2f' % (gpu['used_mem']) + ' GB')
    machine['menu'].show_all()


def build_menu(machine):
    menu = gtk.Menu()
    host_item = gtk.MenuItem(machine['host'])
    menu.append(host_item)
    for gpu in machine['GPUs']:
        gpu['title'] = gtk.MenuItem(gpu['name'] + ', ' + '%.2f' % (gpu['memory']) + ' GB')
        gpu['title'].set_sensitive(False)
        gpu['status'] = gtk.MenuItem(str(gpu['utilization']) + '% , ' + '%.2f' % (gpu['used_mem']) + ' GB')
        menu.append(gpu['title'])
        menu.append(gpu['status'])
    menu.show_all()
    machine['menu'] = menu

def draw_icon(machine,color1,color2):
    '''Draws a graph with 2 columns 1 for each percentage (1 is full, 0 is empty)'''
    WIDTH, HEIGHT = 22, 22
    if machine['nGPUs'] > 2:
        WIDTH = 11*machine['nGPUs'] #if more than 1 GPU on a machine, each column is 11px wide (and not 22px)
    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context (surface)
    ctx.scale (WIDTH/machine['nGPUs'], HEIGHT) # Normalizing the canvas coordinates go from (0,0) to (nGPUs,1)

    for i in range(machine['nGPUs']):
        gpu = machine['GPUs'][i]
        percentage1,percentage2 = gpu['utilization']/100,gpu['used_mem']/gpu['memory']
        ctx.rectangle (i, 1-percentage1, 0.5, percentage1) # Rectangle(x0, y0, x1, y1)
        ctx.set_source_rgb(color1[0]/255,color1[1]/255,color1[2]/255)
        ctx.fill ()

        ctx.rectangle (i+0.5, 1-percentage2, 0.5, percentage2) # Rectangle(x0, y0, x1, y1)
        ctx.set_source_rgb(color2[0]/255,color2[1]/255,color2[2]/255)
        ctx.fill ()
    if 'i' not in machine.keys():
        machine['i'] = 0
    png_name = os.path.join(config_folder,machine['name']+str(machine['i'])+'.png')
    machine['i'] = (machine['i']+1)%2

    surface.write_to_png (png_name) # Output to PNG


    return(png_name)

def new_job(gpu,job):
    notify.Notification.new("<b>New Job for "+gpu['id']+"</b>", job['process_name'] + '\n' + '%.2f' % (job['used_memory']/1024) + ' Go usage', None).show()
    return

def finished_job(gpu,job):
    notify.Notification.new("<b>Finished Job for "+gpu['id']+"</b>", job['process_name'] + '\n' + '%.2f' % (job['used_memory']/1024) + ' Go usage', None).show()    
    return



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    GObject.threads_init()
    main()
