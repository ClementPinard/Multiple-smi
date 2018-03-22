#!/usr/bin/env python
import socket
import json
import sys
import os
import argparse

parser = argparse.ArgumentParser(description='Client for for nvidia multiple smi',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--port', '-p', default=26110, help='port to communicate with, make sure it\'s the same as server_smi scripts')
parser.add_argument('--refresh-rate', '-r', default=10, help='loop rate at which it will check again for connected machines')
parser.add_argument('--max-size', '-m', default=10240, help='max json size')

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


def update_online_machines(args, hosts, online_machines):
    new_online_machines = []
    for name, machine in hosts.items():
        if name in online_machines:
            continue
        try:
            s = socket.create_connection((machine['ip'], args.port))
            s.send(b'smi')

            r = s.recv(args.max_size).decode('utf-8')  # 10ko max
            a = json.loads(r)

        except Exception as e:
            continue

        else:
            machine['socket'] = s
            machine['nGPUs'] = len(a['attached_gpus'])
            machine['GPUs'] = []

            for i, gpu_info in enumerate(a['attached_gpus']):
                gpu = {}
                machine['GPUs'].append(gpu)
                gpu['name'] = gpu_info['product_name']
                if machine['nGPUs'] > 1:
                    gpu['id'] = gpu['name'] + ':' + str(i)
                else:
                    gpu['id'] = gpu['name']
                gpu['memory'] = gpu_info['total_memory']/1024
                gpu['utilization'] = gpu_info['utilization']['gpu']
                gpu['used_mem'] = gpu_info['used_memory']/1024
                gpu['processes'] = gpu_info['processes']
            new_online_machines.append(name)
    return(new_online_machines, online_machines + new_online_machines)


if __name__ == '__main__':
    args = parser.parse_args()
    ticks = 0
    online_machines = []
    while True:
        try:
            if ticks == 0:
                _, online_machines = update_online_machines(args, hosts, online_machines)
            ticks = (ticks + 1) % args.refresh_rate
            for name,m in hosts.items():
                if name in online_machines:
                    s = m['socket']
                    s.send('smi'.encode())

                    r = s.recv(args.max_size).decode('utf-8')
                    a = json.loads(r)
                    for i in range(m['nGPUs']):
                        gpu = m['GPUs'][i]
                        gpu_info = a['attached_gpus'][i]
                        print(gpu['id'])
                        print('gpu: '+str(gpu_info['utilization']['gpu'])+' mem: '+str(100*gpu_info["used_memory"]/(1024*gpu['memory'])) )
                    with open(os.path.join(config_folder,'client_'+name+'.json'),'w') as f:
                        json.dump(a,f,indent=2)

        except KeyboardInterrupt:
            sys.exit()
