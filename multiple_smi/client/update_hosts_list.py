import nmap
import json
import os
import argparse
import socket
import zmq
from .client_utils import get_hosts, update_online_machines


def sniff_port(port=26110, ip=None, search_level=1):
    if ip is None:
        # get personal local ip
        # see https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    decomposed = ip.split('.')
    for i in range(search_level):
        decomposed[-i-1] = '1-254'
    ip_range = '.'.join(decomposed)

    nm = nmap.PortScanner()
    result = nm.scan(ip_range, port, arguments='--open')['scan']
    hosts = {}
    for distant_ip, info in result.items():
        name = info['hostnames'][0]['name'].split('.')[0]
        hosts[name] = {"ip": distant_ip, "port": port}
    return hosts


def test_hosts(args, hosts):
    online, _ = update_online_machines(args, hosts, [])
    if args.verbose:
        print('found machines :')
        for name in online:
            machine = hosts[name]
            print("{} \t ({})".format(name, machine['ip']))
            print("{} GPU(s):".format(machine['nGPUs']))
            for gpu in machine['GPUs']:
                print("{}:\t{:.1f} GB".format(gpu['name'], gpu['memory']))
            print("CPU:")
            print("{}".format(machine['cpu']['name']))
            print("RAM:")
            print("{:.1f} GB".format(machine['ram']['total']))

            print("")

    return online


parser = argparse.ArgumentParser(description='Server for for nvidia multiple smi',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--port', '-p', default='26110', type=str,
                    help='Port to communicate with, make sure it\'s the same as client_smi scripts')
parser.add_argument('--ip', default=None, type=str,
                    help='ip adress from which port will be sniffed. default set to your own adress')
parser.add_argument('--search-level', default=1, type=int,
                    help='range of search for nmap, cannot be above 4, advised to keep it under 1')
parser.add_argument('--verbose', '-v', action='store_true')


def update_json():
    args = parser.parse_args()
    args.context = zmq.Context()
    args.timeout = 2
    old_hosts, config_folder = get_hosts()

    old_ip_list = [v['ip'] for i, v in old_hosts.items()]
    new_hosts = sniff_port(args.port, args.ip, args.search_level)

    for k, v in new_hosts.items():
        if v['ip'] not in old_ip_list:
            old_hosts[k] = v

    file_path = os.path.join(config_folder, 'hosts_to_smi.json')
    with open(file_path, 'w') as f:
            json.dump(old_hosts, f, indent=2)

    if args.verbose:
        test_hosts(args, new_hosts)


if __name__ == "__main__":
    update_json()
