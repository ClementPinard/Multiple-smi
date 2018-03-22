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

STORE_HISTORY = False
port = 26110

if STORE_HISTORY:
    first_smi = my_smi.DeviceQuery()

    home = os.path.expanduser("~")
    server_folder = os.path.join(home,'.server_smi')
    history_file = os.path.join(server_folder,'history.csv')

    ticks = 0
    max_ticks = 60
    start = time.time()
    raw_util = [0] * len(first_smi['attached_gpus'])
    if not os.path.exists(server_folder):
        os.makedirs(server_folder)

    if os.path.exists(history_file):
        with open(history_file, 'r+') as f:
            reader = csv.reader(f)
            lastrow = deque(csv.reader(f), 1)[0]
            print(lastrow)
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
        with open(history_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(columns)


tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.bind(('',port))
tcpsock.listen(5)
clients = {}


while True:
    time.sleep(1)
    smi = my_smi.DeviceQuery()

    if STORE_HISTORY:
        ticks = (ticks + 1) % max_ticks
        if ticks == 0:
            end = time.time()
            duration = end - start
            with open(history_file, 'a') as f:
                writer = csv.writer(f)
                writer.writerow([end, duration] + [u/max_ticks for u in raw_util])
            raw_util = [0] * len(first_smi['attached_gpus'])
            start = end
        for i, gpu_info in enumerate(smi['attached_gpus']):
            raw_util[i] += gpu_info['utilization']['gpu']

    connexions, wlist, xlist = select.select(
        [tcpsock],
        [], [], 0.05)
    print(connexions)

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
            msg = client.recv(1024).decode('utf-8')
            if msg == 'smi':
                data_string = json.dumps(smi)
                client.send(data_string.encode())
