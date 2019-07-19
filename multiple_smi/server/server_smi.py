#!/usr/bin/env python
# coding: utf-8
from . import my_smi
import time
from collections import deque
import csv
import os
import argparse
import zmq
import datetime

parser = argparse.ArgumentParser(description='Server for for Multiple smi',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--port', '-p', default=26110, help='Port to communicate with, make sure it\'s the same as client_smi scripts')
parser.add_argument('--refresh-rate', '-r', default=1, type=float, help='Time rate at which it will listen to sockets (higher is faster)')
parser.add_argument('--store-history', '-s', action='store_true', help='will store gpu usage in a csv file')
parser.add_argument('--history-rate', '--hr', default=60, metavar='N', type=int, help='Will store history usage every N loop')
parser.add_argument('--history-path', '--hp', default=os.path.join(os.path.expanduser('~'), '.server_smi'),
                    help='directory path to store history csv files')
parser.add_argument('--verbose', '-v', action='store_true')


def get_columns(smi):
    columns = ['timestamp', 'duration']
    for i, gpu_info in enumerate(smi['attached_gpus']):
        name = gpu_info['product_name']
        if len(smi['attached_gpus']) > 1:
            id = name + ':' + str(i)
        else:
            id = name
            columns.append(id)
    columns.extend(["cpu", "ram"])
    return columns


def main():
    args = parser.parse_args()
    if args.store_history or args.verbose:
        first_smi = my_smi.DeviceQuery()

        ticks = 0
        max_ticks = args.history_rate
        start = time.time()
        raw_util = [0] * (len(first_smi['attached_gpus']) + 2)
        columns = get_columns(first_smi)
        if args.store_history:
            if not os.path.exists(args.history_path):
                os.makedirs(args.history_path)

            today = datetime.datetime.today().strftime('%Y-%m-%d')
            history_path = os.path.join(args.history_path, today + '.csv')
            if os.path.exists(history_path):
                with open(history_path, 'r+') as f:
                    reader = csv.reader(f)
                    lastrow = deque(reader, 1)[0]
                    try:
                        # If this fails, it means the csv only had the column names
                        start = float(lastrow[0]) + float(lastrow[1])
                        duration = time.time() - start
                        writer = csv.writer(f)
                        writer.writerow([start, duration] + [0]*(len(lastrow) - 2))
                    except ValueError:
                        pass
            else:
                with open(history_path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
        if args.verbose:
            print("\t".join(columns))

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(args.port))
    topic = "smi"

    while True:
        time.sleep(1/args.refresh_rate)
        smi = my_smi.DeviceQuery()
        socket.send_string(str(topic), zmq.SNDMORE)
        socket.send_pyobj(smi)

        if args.store_history or args.verbose:
            ticks = (ticks + 1) % max_ticks
            if ticks == 0:
                end = time.time()
                duration = end - start
                row = [end, duration] + [u/max_ticks for u in raw_util]
                row_string = ["{:.2f}".format(v) for v in row]
                if args.store_history:
                    today = datetime.date.today().strftime('%Y-%m-%d')
                    history_path = os.path.join(args.history_path, today + '.csv')
                    with open(history_path, 'a') as f:
                        writer = csv.writer(f)
                        writer.writerow(row_string)
                if args.verbose:
                    print('\t'.join(row_string))
                raw_util = [0] * (len(first_smi['attached_gpus']) + 2)
                start = end
            for i, gpu_info in enumerate(smi['attached_gpus']):
                raw_util[i] += gpu_info['utilization']['gpu']
            raw_util[-2] += smi['cpu']['usage']
            raw_util[-1] += smi['ram']['usage']


if __name__ == '__main__':
    main()
