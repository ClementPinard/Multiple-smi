from setuptools import setup

setup(name='super-smi',
      description='Python Bindings for the NVIDIA Management Library',
      py_modules=['my_smi'],
      scripts=['server_smi.py','client_smi.py','client_smi_appindicator.py'],
      data_files=[('data',['empty.png','hosts_to_smi.json']),
                  ('/etc/systemd/system', ['server_smi.service'])],
      install_requires=[
          'nvidia-ml-py3',
      ]
      )
