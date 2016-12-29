from distutils.core import setup
from sys import version

setup(name='super-smi',
      description='Python Bindings for the NVIDIA Management Library',
      py_modules=['pynvml', 'nvidia_smi', 'my_smi'],
      scripts=['server_smi.py','client_smi.py','client_smi_appindicator.py'],
      data_files=[('data',['empty.png','hosts_to_smi.json']),
                  ('/etc/systemd/system', ['server_smi.service'])]
      )

