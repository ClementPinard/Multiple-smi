# Nvidia multiple smi

### Python bindings for pyNVML library over network
intended to work with python 3+

Based on [pyNVML](https://pypi.python.org/pypi/nvidia-ml-py3)

### Features
- Allows you to get `nvidia-smi` output for multiple connected computers at once, and display it on a nice appindicator for Unity/Gnome users.

![status](https://github.com/ClementPinard/nvidia-multiple-smi/blob/master/images/status%20bar.png)

- Allows you to get a notification every time a new process is launched or finished. A minimum of 200MB memory use is needed for the notification to appear.

![notif](https://github.com/ClementPinard/nvidia-multiple-smi/blob/master/images/Sans%20titre.png)

- This tool is aimed at small research teams, with multiple GPU-equipped computers, which you can manually ssh to. At a glance you can see every usage of your computer stock, and where you can launch your computation. It also provides some basis if you want to develop a tool to automatically launch your computation on the least busy computer of your network.


### installation:

`sudo python3 setup.py install`

#### Optional note for Ubuntu 18+ users

If you want to use the gui, as unity is replaced by Gnome-shell, you need to enable appindicators on gnome-shell with `gnome-tweak-tool`, and you need to install python bindings for Appindicator3 :

```bash
sudo apt install gir1.2-appindicator3-0.1
```

#### Server side services installation

To allow clients to access your computer's smi stats, simply run
`server_smi`

But you can also enable it as a service that will be launched at boot.

---------------------------

- **Ubuntu 16+** :  the service file allow the server_smi to run automatically during boot
```
sudo systemctl daemon-reload
sudo systemctl enable server_smi.service
```
to uninstall: 
```
sudo systemctl disable server_smi.service
```

- **Ubuntu 14** : you have to daemonize the script and put it in init.d
```
sudo cp server_smi_daemon.sh /etc/init.d/.
sudo chmod 0755 /etc/init.d/server_smi_daemon.sh
sudo update-rc.d server_smi_daemon.sh defaults
```
to uninstall:
```
sudo update-rc.d -f service_smi_daemon.sh remove
```

### to run the appindicator
(gnome and unity environment only for the moment):

`client_smi_gui`

### to run the client_smi (CLI version):

`client_smi`


### Configuration:

To add your own hosts, simply run a smi_client (CLI or gnome) once and add your entries in the json file that should be here:
`~/.client_smi/hosts_to_smi.json`

Default ones are ml1 and ml2 with associated colors

### Gpu usage stats:

Server-side, gpu usage history is stored in `~/.server_smi/history.csv` if launched from CLI, `/etc/server_smi/history.csv` if launched from systemctl/init.d.  Usage is written on it every ~60 sec, feel free to make some data science with it.

To disable it, you can remove option `-s` in server_smi.service (line 7) or server_smi_daemon.sh (line 6) before installing