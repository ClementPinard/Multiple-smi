#!/usr/bin/env python
# coding: utf-8 

import socket
import threading
import my_smi
import json
import time

class ClientThread(threading.Thread):

    def __init__(self, ip, port, clientsocket):

        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.clientsocket = clientsocket

    def run(self): 
        while True:
            try:
                time.sleep(1)
                r = self.clientsocket.recv(9999999)
                print(r)
                
                if 'break' in r:
                    break
                
                smi = my_smi.DeviceQuery()
                data_string = json.dumps(smi)
                
                self.clientsocket.send(data_string)

            except Exception:
                break
            

tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpsock.bind(("",1111))

while True:
    tcpsock.listen(10)
    (clientsocket, (ip, port)) = tcpsock.accept()
    newthread = ClientThread(ip, port, clientsocket)
    newthread.start()
