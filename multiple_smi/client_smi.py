#!/usr/bin/env python
import json
import sys
import os
import argparse
from .client_utils import get_hosts, update_online_machines

parser = argparse.ArgumentParser(description='Client for for nvidia multiple smi',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--port', '-p', default=26110, help='port to communicate with, make sure it\'s the same as server_smi scripts')
parser.add_argument('--refresh-rate', '-r', default=10, help='loop rate at which it will check again for connected machines')
parser.add_argument('--max-size', '-m', default=10240, help='max json size')
parser.add_argument('--timeout', '-t', default=2, help='timeout for servers response. useful when blocked by a firewall')
parser.add_argument('-v', '--verbose', action='store_true', help='Display machine scanning status on CLI')


def main():
    args = parser.parse_args()
    hosts, config_folder = get_hosts()
    ticks = 0
    online_machines = []
    while True:
        try:
            if ticks == 0:
                _, online_machines = update_online_machines(args, hosts, online_machines)
            ticks = (ticks + 1) % args.refresh_rate
            for name, m in hosts.items():
                if name in online_machines:
                    s = m['socket']
                    s.send('smi'.encode())

                    r = s.recv(args.max_size).decode('utf-8')
                    a = json.loads(r)
                    for i in range(m['nGPUs']):
                        gpu = m['GPUs'][i]
                        gpu_info = a['attached_gpus'][i]
                        print(gpu['id'])
                        print('gpu: {} % mem: {:.2f} %'.format(gpu_info['utilization']['gpu'],
                                                               100*gpu_info["used_memory"]/(1024*gpu['memory'])))
                    with open(os.path.join(config_folder, 'client_'+name+'.json'), 'w') as f:
                        json.dump(a, f, indent=2)

        except KeyboardInterrupt:
            sys.exit()


if __name__ == '__main__':
    main()
