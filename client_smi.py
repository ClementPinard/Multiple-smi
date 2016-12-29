#!/usr/bin/env python
import socket
import json
import sys
import os

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
        json.dump(hosts,f,indent=2)

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

while True:
    try:
        for m in machines:
            s = m['socket']
            s.send("smi")
        
            r = s.recv(9999999)
            a = json.loads(r)
            for i in range(m['nGPUs']):
                gpu = m['GPUs'][i]
                gpu_info = a['attached_gpus'][i]
                print(gpu['id'])
                print('gpu: '+str(gpu_info['utilization']['gpu'])+' mem: '+str(100*gpu_info["used_memory"]/(1024*gpu['memory'])) )
            with open(os.path.join(config_folder,'client_'+m['name']+'.json'),'wb') as f:
                json.dump(a,f,indent=2)
            
    except KeyboardInterrupt:
        sys.exit()

