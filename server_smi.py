#!/usr/bin/env python
# coding: utf-8

import socket
import select
import my_smi
import json
import time
from collections import deque
import csv
import os
import argparse

parser = argparse.ArgumentParser(description='Server for for nvidia multiple smi',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--port', '-p', default=26110, help='Port to communicate with, make sure it\'s the same as client_smi scripts')
parser.add_argument('--refresh-rate', '-r', default=1, help='Time rate at which it will listen to sockets')
parser.add_argument('--store-history', '-s', action='store_true', help='will store gpu usage in a csv file')
parser.add_argument('--history-rate', '--hr', default=60, metavar='N', help='Will store history usage every N loop')
parser.add_argument('--history-path', '--hp', default=os.path.join(os.path.expanduser('~'),'.server_smi','history.csv'),
                    help='csv path to store history')


def main():
    args = parser.parse_args()
    if args.store_history:
        first_smi = my_smi.DeviceQuery()

        server_folder = os.path.dirname(args.history_path)

        ticks = 0
        max_ticks = args.history_rate
        start = time.time()
        raw_util = [0] * len(first_smi['attached_gpus'])
        if not os.path.exists(server_folder):
            os.makedirs(server_folder)

        if os.path.exists(args.history_path):
            with open(args.history_path, 'r+') as f:
                reader = csv.reader(f)
                lastrow = deque(reader, 1)[0]
                start = float(lastrow[0]) + float(lastrow[1])
                duration = time.time() - start
                writer = csv.writer(f)
                writer.writerow([start, duration] + [0]*(len(lastrow) - 2))
        else:
            columns = ['timestamp', 'duration']

            for i, gpu_info in enumerate(first_smi['attached_gpus']):
                name = gpu_info['product_name']
                if len(first_smi['attached_gpus']) > 1:
                    id = name + ':' + str(i)
                else:
                    id = name
                columns.append(id)
            with open(args.history_path, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(columns)

    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.bind(('',args.port))
    tcpsock.listen(5)
    clients = {}

    while True:
        time.sleep(1/args.refresh_rate)
        smi = my_smi.DeviceQuery()

        if args.store_history:
            ticks = (ticks + 1) % max_ticks
            if ticks == 0:
                end = time.time()
                duration = end - start
                with open(args.history_path, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow([end, duration] + [u/max_ticks for u in raw_util])
                raw_util = [0] * len(first_smi['attached_gpus'])
                start = end
            for i, gpu_info in enumerate(smi['attached_gpus']):
                raw_util[i] += gpu_info['utilization']['gpu']

        connexions, wlist, xlist = select.select(
            [tcpsock],
            [], [], 0.05)

        for connexion in connexions:
            conn, infos = connexion.accept()
            if infos[0] in clients.keys():
                clients[infos[0]].close()
            clients[infos[0]] = conn

        clients_rlist = []
        try:
            clients_rlist, wlist, xlist = select.select(clients.values(), [], [], 0.05)
        except select.error:
            pass
        else:
            for client in clients_rlist:
                msg = client.recv(1024)
                try:
                    msg = msg.decode('utf-8')
                    if msg == 'smi':
                        data_string = json.dumps(smi)
                        client.send(data_string.encode())
                except Exception as e:
                    pass


if __name__ == '__main__':
    main()