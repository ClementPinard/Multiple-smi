import json
import os


class BaseFrontend:
    def __init__(self, config_folder, *args, **kwargs):
        self.config_folder = config_folder
        self.paths = {}

    def launch(self, func, *args, **kwargs):
        kwargs["frontend"] = self
        return func(*args, **kwargs)

    def update_menu(self, machine_name, machine):
        print(f"{machine_name}@{machine['ip']}")
        summary = machine["summary"]
        for gpu in summary["GPUs"]:
            print(gpu["id"])
            print(
                "gpu: {} % mem: {:.2f} %".format(
                    gpu["utilization"], 100 * gpu["used_mem"] / gpu["memory"]
                )
            )
        print(f"cpu: {summary['cpu']['usage']} %")
        print(f"ram: {summary['ram']['usage']} %")
        print("")
        with open(
            os.path.join(self.config_folder, "client_" + machine_name + ".json"), "w"
        ) as f:
            json.dump(machine["full_stats"], f, indent=2)

    def new_machines(self, machine_names, machines):
        return

    def lost_machine(self, machine_name, machine):
        print(f"{machine_name} Deconnected")

    def __del__(self):
        for key, path in self.paths.items():
            if os.path.isfile(path):
                os.remove(path)
