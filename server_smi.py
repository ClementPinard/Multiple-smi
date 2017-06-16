#!/usr/bin/env python
# coding: utf-8 

import socket
import select
import my_smi
import json
import time

port = 26110  

tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.bind(('',port))
tcpsock.listen(5)
clients = {}

while True:
    time.sleep(1)
    connexions, wlist, xlist = select.select([tcpsock],
        [], [], 0.05)
    print(connexions)
    
    for connexion in connexions:
        conn, infos = connexion.accept()
        if infos[0] in clients.keys():
            clients[infos[0]].close()
        clients[infos[0]] = conn

    print('clients: ' + str(clients))

    clients_rlist = []
    try:
        clients_rlist, wlist, xlist = select.select(clients.values(),[], [], 0.05)
    except select.error:
        pass
    else:
        for client in clients_rlist:
            msg = client.recv(1024)
            print(msg)
            if msg == 'smi':
                smi = my_smi.DeviceQuery()
                data_string = json.dumps(smi)
                client.send(data_string)