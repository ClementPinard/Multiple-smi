import os
import sys
import subprocess
from subprocess import CalledProcessError
import argparse

service_string = '''[Unit]
Description=Multiple smi server side
After=multi-user.target

[Service]
Type=simple
ExecStart={server_smi_path} {history_string} -p {port} -r {rate}
Restart=always

[Install]
WantedBy=multi-user.target'''

parser = argparse.ArgumentParser(description='Install server smi as a service to enable it at boot',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--server-smi-path', default=None, help="path to server_smi binary file. If not set, will take the output of 'which server_smi'")
parser.add_argument('--systemd-path', default="/etc/systemd/system", help="path to systemd service files")
parser.add_argument('--port', '-p', default=26110, help='Port to communicate with, make sure it\'s the same as client_smi scripts')
parser.add_argument('--refresh-rate', '-r', default=1, type=int, help='Time rate at which it will listen to sockets')
parser.add_argument('--store-history', '-s', action='store_true', help='will store gpu usage in a csv file')
parser.add_argument('--history-rate', '--hr', default=60, type=int, metavar='N', help='Will store history usage every N loop')
parser.add_argument('--history-path', '--hp', default='/etc/.server_smi',
                    help='directory path to store history csv files')
parser.add_argument('--uninstall', '-u', action='store_true', help='If selected, will deisable the service and delete the service file')


def uninstall(args):
    try:
        subprocess.check_call(["systemctl", "stop", "server_smi.service"])
        subprocess.check_call(["systemctl", "disable", "server_smi.service"])
        if os.path.isfile(args.service_file_path):
            os.remove(args.service_file_path)
            subprocess.call(["systemctl", "daemon-reload"])
            print("'server_smi.service' file was correctly deleted from systemctl")
        else:
            raise Exception("'server_smi.service' file not found and was not removed,\n"
                            "although it is still available for systemctl.\n"
                            "Check specified systemd folder argument")
    except CalledProcessError:
        raise Exception("Service file not available for systemctl,\n"
                        "it was probably already uninstalled")


def install(args):
    if args.server_smi_path is None:
        try:
            args.server_smi_path = subprocess.check_output(['which', 'server_smi']).decode()[:-1]
        except CalledProcessError:
            raise Exception("server_smi script not found, probably because you didn't install server_smi in sudo.\n"
                            "You might want to specify the litteral path to user-installed server_smi")

    if args.store_history:
        history_param_string = "-s --hr {} --hp {}".format(args.history_rate, args.history_path)
    else:
        history_param_string = ""

    service_final_string = service_string.format(server_smi_path=args.server_smi_path,
                                                 history_string=history_param_string,
                                                 port=args.port,
                                                 rate=args.refresh_rate)
    with open(args.service_file_path, 'w') as f:
            f.write(service_final_string)

    subprocess.call(["systemctl", "daemon-reload"])
    subprocess.call(["systemctl", "enable", "server_smi.service"])

    print("server_smi is now installed and will run at next reboot.")
    print("You can access its stauts with the following command (no sudo needed)")
    print("")
    print("systemctl status server_smi.service")
    print("")
    answer = None
    while answer is None:
        raw_answer = input("Run it now? (will launch \"systemctl start server_smi.service)\" [Y/n]")
        if raw_answer.lower() in ['y', 'o', '']:
            answer = True
            subprocess.call(["systemctl", "start", "server_smi.service"])
        elif raw_answer.lower() == 'n':
            answer = False


def main():
    args = parser.parse_args()
    if os.geteuid() != 0:
        sys.exit("You need to have root privileges to run this script.\n"
                 "Please try again, this time using 'sudo'. Exiting.")

    args.service_file_path = os.path.join(args.systemd_path, 'server_smi.service')
    if args.uninstall:
        uninstall(args)
    else:
        install(args)
