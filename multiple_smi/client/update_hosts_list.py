import argparse
import json
import os
import socket
from copy import deepcopy

import zmq

from .client_utils import get_hosts, get_new_machines, update_online_machines

try:
    import nmap
except Exception as e:
    print("you need to install nmap with apt or brew")
    raise e


def sniff_port(port=26110, ip=None, search_level=1):
    # get personal local ip
    # see https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.255.255.255", 1))
    self_ip = s.getsockname()[0]
    if ip is None:
        ip = self_ip
    decomposed = ip.split(".")
    for i in range(search_level):
        decomposed[-i - 1] = "1-254"
    ip_range = ".".join(decomposed)

    nm = nmap.PortScanner()
    result = nm.scan(ip_range, port, arguments="--open")["scan"]
    hosts = {}
    for distant_ip, info in result.items():
        if distant_ip == self_ip:
            distant_ip = "localhost"
        name = info["hostnames"][0]["name"].split(".")[0]
        hosts[name] = {"ip": distant_ip, "port": port}
    return hosts


def test_hosts(args, hosts):
    online = update_online_machines(args, hosts, [])
    online = get_new_machines(online)
    if args.verbose:
        print("found machines :")
        for name in online:
            summary = hosts[name]["summary"]
            print(f"{name} \t ({summary['ip']})")
            print(f"{summary['nGPUs']} GPU(s):")
            for gpu in summary["GPUs"]:
                print(f"{gpu['name']}:\t{gpu['memory']:.1f} GB")
            print("CPU:")
            print(f"{summary['cpu']['name']}")
            print("RAM:")
            print(f"{summary['ram']['total']:.1f} GB")

            print("")

    return online


parser = argparse.ArgumentParser(
    description="Server for for nvidia multiple smi",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "--port",
    "-p",
    default="26110",
    type=str,
    help="Port to communicate with, make sure it's the same as client_smi scripts",
)
parser.add_argument(
    "--ip",
    default=None,
    type=str,
    help="ip adress from which port will be sniffed. default set to your own adress",
)
parser.add_argument(
    "--search-level",
    default=1,
    type=int,
    help="range of search for nmap, cannot be above 4, advised to keep it under 1",
)
parser.add_argument(
    "--dry",
    "-d",
    action="store_true",
    help="perform a dry run: don't update the JSON file",
)
parser.add_argument("--verbose", "-v", action="store_true")


def main():
    args = parser.parse_args()
    args.context = zmq.Context()
    args.timeout = 2
    old_hosts, _, config_folder = get_hosts(args)

    old_ip_list = [v["ip"] for i, v in old_hosts.items()]
    new_hosts = sniff_port(args.port, args.ip, args.search_level)
    online = test_hosts(args, deepcopy(new_hosts))

    if not args.dry:
        for k, v in new_hosts.items():
            if v["ip"] not in old_ip_list and k in online:
                old_hosts[k] = v

        file_path = os.path.join(config_folder, "hosts_to_smi.json")
        print(old_hosts)
        with open(file_path, "w") as f:
            json.dump(old_hosts, f, indent=2)


if __name__ == "__main__":
    main()
