from .default_frontend import BaseFrontend
from .icon_utils import draw_icon
import os
import stat
import json
import sys

argos_template = '''#!{python}

import re
import time
import base64
import json
import sys

with open("{icon_path}", 'rb') as bytes:
    img_str = base64.b64encode(bytes.read())
print("{name} | image='{{}}'\\n---".format(img_str.decode()))

try:
    with open("{json_path}") as f:
        info = json.load(f)
except:
    sys.exit()

print("{name}@{ip}")
for gpu in info['GPUs']:
    print("{{}}, {{:.2f}} GB | color=gray".format(gpu['name'], gpu['memory']))
    print("{{}}% , {{:.2f}} GB".format(gpu['utilization'], gpu['used_mem']))

print("---")
print(info['cpu']['name'] + '| color=gray')
print("{{}}%".format(info['cpu']['usage']))
print("---")
print("RAM | color=gray")
print("{{}}% ({{:.2f}} GB / {{:.2f}} GB)".format(info['ram']['usage'],
                                           info['ram']['used'],
                                           info['ram']['total']))
'''


class ArgosFrontend(BaseFrontend):
    """docstring for ArgosBackend"""

    def __init__(self, config_folder, argos_folder=None):
        super(ArgosFrontend, self).__init__(config_folder)
        self.argos_folder = argos_folder or os.path.join(os.path.expanduser('~'), ".config", "argos")
        assert(os.path.isdir(self.argos_folder))

    def build_menu(self, machine_name, machine):
        icon_path_string = os.path.join(self.config_folder, "{}.png".format(machine_name))
        json_path_string = os.path.join(self.config_folder, "client_{}.json".format(machine_name))
        script_string = argos_template.format(python=sys.executable,
                                              home=os.path.expanduser("~"),
                                              icon_path=icon_path_string,
                                              json_path=json_path_string,
                                              name=machine_name,
                                              ip=machine['ip'])
        script_path = os.path.join(self.argos_folder, "{}.1s.py".format(machine_name))
        with open(script_path, 'w') as f:
            f.write(script_string)

        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)

        self.paths[machine_name] = script_path

    def update_menu(self, machine_name, machine):
        png_path = os.path.join(self.config_folder, "{}.png".format(machine_name))
        draw_icon(machine).write_to_png(png_path)
        json_path = os.path.join(self.config_folder, "client_{}.json".format(machine_name))
        with open(json_path, 'w') as f:
            json.dump(machine['summary'], f, indent=2)

    def new_machines(self, machine_names, machines):
        for name in machine_names:

            self.update_menu(name, machines[name])
            self.build_menu(name, machines[name])

    def lost_machine(self, machine_name, machine):
        if machine_name in self.paths.keys():
            if os.path.isfile(self.paths[machine_name]):
                os.remove(self.paths[machine_name])
            del self.paths[machine_name]
