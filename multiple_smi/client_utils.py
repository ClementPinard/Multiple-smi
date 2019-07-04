import socket
import json
import os
import time

default_machines = {
    "Me": {"ip": "localhost",
           "colors": [[108, 208, 84], [202, 255, 112]]
           }
}


def get_hosts():
    home = os.path.expanduser("~")
    config_folder = os.path.join(home, '.client_smi')
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    file_path = os.path.join(config_folder, 'hosts_to_smi.json')
    if(os.path.exists(file_path)):
        with open(file_path) as f:
            hosts = json.load(f)
    else:
        hosts = default_machines
        with open(file_path, 'w') as f:
            json.dump(hosts, f, indent=2)
    return hosts, config_folder


def update_online_machines(args, hosts, online_machines):
    new_online_machines = []
    for name, machine in hosts.items():
        if name in online_machines:
            continue
        try:
            if args.verbose:
                print("connecting to {}... (ip {})    ".format(name, machine['ip']), end='')
            time.sleep(1)
            s = socket.create_connection((machine['ip'], args.port), timeout=args.timeout)
            s.send(b'smi')

            r = s.recv(args.max_size).decode('utf-8')  # 10ko max
            a = json.loads(r)
            if args.verbose:
                print('OK')

        except Exception:
            if args.verbose:
                print('FAIL')
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
                    gpu['id'] = "{}:{}".format(gpu['name'], i)
                else:
                    gpu['id'] = gpu['name']
                gpu['memory'] = gpu_info['total_memory']/1024
                gpu['utilization'] = gpu_info['utilization']['gpu']
                gpu['used_mem'] = gpu_info['used_memory']/1024
                gpu['processes'] = gpu_info['processes']
            new_online_machines.append(name)
    return(new_online_machines, online_machines + new_online_machines)
