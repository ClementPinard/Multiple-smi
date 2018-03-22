from setuptools import setup

setup(name='nvidia-multiple-smi',
      version='1.1',
      url='https://github.com/ClementPinard/nvidia-multiple-smi',
      license='MIT',
      author='Clément Pinard',
      author_email='clempinard@gmail.com',
      description='Python Bindings for the NVIDIA Management Library over the network',
      py_modules=['my_smi'],
      scripts=['server_smi.py','client_smi.py','client_smi_appindicator.py'],
      data_files=[('data',['empty.png','hosts_to_smi.json']),
                  ('/etc/systemd/system', ['server_smi.service'])],
      install_requires=[
          'nvidia-ml-py3',
      ]
      )
