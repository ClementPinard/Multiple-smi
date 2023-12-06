import json
import os
import time
from queue import Empty, Queue

import zmq
from zmq import ssh


def get_hosts(save_options=False, **args):
    home = os.path.expanduser("~")
    config_folder = os.path.join(home, ".client_smi")
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    file_path = os.path.join(config_folder, "hosts_to_smi.json")
    if os.path.exists(file_path):
        with open(file_path) as f:
            hosts = json.load(f)
    else:
        hosts = {}
        with open(file_path, "w") as f:
            json.dump(hosts, f, indent=2)
    config_file_path = os.path.join(config_folder, "client_options.json")
    if save_options and len(args) > 0:
        with open(config_file_path, "w") as f:
            json.dump(dict(args), f, indent=2)
        options = args
    else:
        if os.path.exists(config_file_path):
            with open(config_file_path) as f:
                options = json.load(f)
                options.update(args)
        else:
            options = args

    return hosts, options, config_folder


def get_new_machines(new_machines_queue):
    result = []
    while True:
        try:
            result.append(new_machines_queue.get_nowait())
        except Empty:
            break
    return result


def update_online_machines(args, hosts, online_machines, new_machines=Queue()):
    current_new_machines = []
    for name, machine in hosts.items():
        if name in online_machines:
            continue
        try:
            if "port" not in machine.keys():
                machine["port"] = args.port
            log_string = f"connecting to {name}... (ip {machine['ip']})    "
            time.sleep(1)
            socket = args.context.socket(zmq.SUB)
            if "tunnel" in vars(args).keys() and args.tunnel:
                ssh.tunnel_connection(
                    socket, f"tcp://{machine['ip']}:{args.port}", args.tunnel
                )
            else:
                socket.connect(f"tcp://{machine['ip']}:{args.port}")

            socket.setsockopt_string(zmq.SUBSCRIBE, "smi")
            poller = zmq.Poller()
            poller.register(socket, zmq.POLLIN)
            if poller.poll(1000 * args.timeout):
                _ = socket.recv_string()
                info = socket.recv_pyobj()
            else:
                raise OSError("Timeout processing auth request")
            if args.verbose:
                print(f"{log_string} OK")

        except Exception as e:
            if args.verbose:
                print(f"{log_string} FAIL: {e}")
            continue

        else:
            machine["socket"] = socket
            machine["poller"] = poller
            machine["full_stats"] = info

            if "summary" not in machine.keys():
                machine["summary"] = {"ip": machine["ip"], "name": name}

            summary = machine["summary"]

            summary["cpu"] = info["cpu"]
            summary["ram"] = info["ram"]
            summary["nGPUs"] = len(info["attached_gpus"])
            summary["GPUs"] = []

            for i, gpu_info in enumerate(info["attached_gpus"]):
                gpu = {}
                summary["GPUs"].append(gpu)
                gpu["name"] = gpu_info["product_name"]
                if summary["nGPUs"] > 1:
                    gpu["id"] = f"{gpu['name']}:{i}"
                else:
                    gpu["id"] = gpu["name"]
                gpu["memory"] = gpu_info["total_memory"] / 1024
                gpu["utilization"] = gpu_info["utilization"]["gpu"]
                gpu["used_mem"] = gpu_info["used_memory"] / 1024
                gpu["processes"] = gpu_info["processes"]
            current_new_machines.append(name)
    for m in current_new_machines:
        new_machines.put(m)
    return new_machines
