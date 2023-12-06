#!/usr/bin/env python
import argparse
import os
import sys
import time
from queue import Queue
from threading import Thread

import zmq

from .client_utils import get_hosts, get_new_machines, update_online_machines
from .notifier_util import init_notifier

parser = argparse.ArgumentParser(
    description="Client for for Multiple smi",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "--port",
    "-p",
    default=26110,
    type=int,
    help="port to communicate with, make sure it's the same as server_smi scripts",
)
parser.add_argument(
    "--refresh-period",
    "-r",
    default=30,
    type=int,
    help="time in seconds before it checks again for connected machines",
)
parser.add_argument(
    "--timeout",
    "-t",
    default=2,
    type=float,
    help="timeout for servers response. useful when blocked by a firewall",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Display machine scanning status on CLI",
)
parser.add_argument(
    "--tunnel",
    default=None,
    help="Make a ssh tunnel through a specified server (ex: Me@localhost)",
)
parser.add_argument(
    "--hosts-list-path",
    "-j",
    default=None,
    help="path to json file containing hosts info, ip, ports and icon colors",
)

parser.add_argument(
    "--notif-backend",
    default=None,
    choices=["gnome", "ntfy"],
    help="which beckend to choose for notifications",
)
parser.add_argument(
    "--frontend",
    default="default",
    choices=["default", "appindicator", "argos"],
    help="frontend to use to render the menu. argos compatible with bitbar",
)
parser.add_argument(
    "--argos-folder",
    default=os.path.join(os.path.expanduser("~"), ".config", "argos"),
    help="config folder of argos or Bitbar",
)
parser.add_argument(
    "--min-mem-notif",
    "-n",
    default=1,
    type=float,
    help="min memory usage to trigger Notification (in GB)",
)
parser.add_argument("--save-options", action="store_true")


def smi(args, hosts, frontend):
    online_machines = []
    new_machines_queue = Queue()
    start = time.time()
    elapsed = None
    while True:
        if elapsed is None or elapsed > args.refresh_period:
            thread = Thread(
                target=update_online_machines,
                args=(args, hosts, online_machines, new_machines_queue),
            )
            thread.daemon = True
            thread.start()
            start = time.time()

        new_machines = get_new_machines(new_machines_queue)
        frontend.new_machines(new_machines, hosts)
        notify_new_machines(args, new_machines, hosts)
        online_machines.extend(new_machines)
        new_machines = []

        elapsed = time.time() - start
        for name, machine in hosts.items():
            if name in online_machines:
                s = machine["socket"]
                p = machine["poller"]
                if p.poll(1000 * args.timeout):
                    _ = s.recv_string()
                    info = s.recv_pyobj()
                    machine["full_stats"] = info
                else:
                    frontend.lost_machine(name, hosts[name])
                    notify_lost_machine(args, name, machine)
                    online_machines.remove(name)
                    continue
                summary = machine["summary"]
                for i in range(summary["nGPUs"]):
                    gpu_info = info["attached_gpus"][i]
                    gpu = summary["GPUs"][i]
                    gpu["utilization"] = gpu_info["utilization"]["gpu"]
                    gpu["used_mem"] = gpu_info["used_memory"] / 1024
                    update_processes_list(args, name, gpu, gpu_info["processes"])
                summary["ram"] = info["ram"]
                summary["cpu"] = info["cpu"]

                frontend.update_menu(name, machine)


def update_processes_list(args, machine_name, gpu, new):
    old = gpu["processes"]
    for p in new.keys():
        if p not in old.keys() and new[p]["used_memory"] / 1024 > args.min_mem_notif:
            notify_new_job(args, machine_name, gpu, new[p])
            if args.verbose:
                print(f"new: ({gpu['id']})\t{new[p]}")
            gpu["processes"][p] = new[p]
        elif p in old.keys():
            gpu["processes"][p] = new[p]
    for p in list(old.keys()):
        if p not in new.keys() and old[p]["used_memory"] / 1024 > args.min_mem_notif:
            notify_finished_job(args, machine_name, gpu, old[p])
            if args.verbose:
                print(f"finished: ({gpu['id']})\t{old[p]}")
            gpu["processes"].pop(p, None)


def notify_new_job(args, machine_name, gpu, job):
    args.notify(
        f"New Job for {machine_name}",
        f"{gpu['id']}\n{job['process_name']}\n{job['used_memory'] / 1024:.2f} Go usage",
        "applications-science",
    )
    return


def notify_finished_job(args, machine_name, gpu, job):
    args.notify(
        f"Finished Job for {machine_name}",
        f"{gpu['id']}\n{job['process_name']}\n{job['used_memory'] / 1024:.2f} Go usage",
        "applications-science",
    )
    return


def notify_new_machines(args, machine_names, hosts):
    if len(machine_names) == 1:
        args.notify(
            f"{machine_names[0]} Connected", hosts[machine_names[0]]["ip"], "computer"
        )
    elif len(machine_names) > 1:
        args.notify(
            "New machines",
            "\t\n".join([f"{name}\t({hosts[name]['ip']})" for name in machine_names]),
            "computer",
        )
    return


def notify_lost_machine(args, machine_name, machine):
    args.notify(f"{machine_name} Disconnected", machine["ip"], "dialog-warning")
    return


def get_non_default(args_dict):
    return {k: v for k, v in args_dict.items() if v != parser.get_default(k)}


def main():
    args = parser.parse_args()
    args_dict = vars(args)
    hosts, saved_args, config_folder = get_hosts(**get_non_default(args_dict))
    new_args = {**args_dict, **saved_args}
    args = argparse.Namespace(**new_args)
    args.notify = init_notifier(args.notif_backend)
    args.context = zmq.Context()

    if args.frontend == "default":
        from .menu_frontend.default_frontend import BaseFrontend

        frontend = BaseFrontend(config_folder)
    else:
        from .menu_frontend.icon_utils import give_default_colors

        give_default_colors(hosts)
        if args.frontend == "appindicator":
            from .menu_frontend.appindicator import AppIdFrontend

            frontend = AppIdFrontend(config_folder)
        elif args.frontend == "argos":
            from .menu_frontend.argos import ArgosFrontend

            frontend = ArgosFrontend(config_folder, args.argos_folder)

    try:
        frontend.launch(smi, args, hosts)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
