#Nvidia multiple smi
###Python bindings for pyNVML library over network
intended to work with python 2.7

Based on [pyNVML](https://pypi.python.org/pypi/nvidia-ml-py/4.304.04)

###Features
- Allows you to get `nvidia-smi` output for multiple connected computers at once, and display it on a nice appindicator for Unity/Gnome users.

![status](https://github.com/ClementPinard/nvidia-multiple-smi/blob/master/images/status%20bar.png)

- Allows you to get a notification every time a new process is launched or finished. A minimum of 200MB memory use is needed for the notification to appear.

![notif](https://github.com/ClementPinard/nvidia-multiple-smi/blob/master/images/Sans%20titre.png)

- This tool is aimed at small research teams, with multiple GPU-equipped computers, which you can manually ssh to. At a glance you can see every usage of your computer stock, and where you can launch your computation. It also provides some basis if you want to develop a tool to automatically launch your computation on the least busy computer of your network.


###installation:

`sudo python setup.py install`

####Server side services installation

To allow clients to access your computer's smi stats, simply run
`server_smi.py`

But you can also enable it as a service that will be launched at boot.

---------------------------

- **Ubuntu 15+** :  the service file allow the server_smi to run automatically during boot
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

###to run the appindicator
(gnome and unity environment only for the moment):

`client_smi_appindicator.py`

###to run the client_smi (CLI version):

`client_smi.py`


###Configuration:

To add your own hosts, simply run a smi_client (CLI or gnome) once and add your entries in the json file that should be here:
`~/.client_smi/hosts_to_smi.json`

Default ones are ml1 and ml2 with associated colors
