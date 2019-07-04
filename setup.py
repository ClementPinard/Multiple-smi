from setuptools import setup

setup(name='nvidia-multiple-smi',
      version='1.1',
      url='https://github.com/ClementPinard/nvidia-multiple-smi',
      license='MIT',
      author='Clément Pinard',
      author_email='clempinard@gmail.com',
      description='Look up GPU usage on multiple servers at the same time',
      packages=['multiple_smi'],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'client_smi = multiple_smi.client_smi:main',
              'server_smi = multiple_smi.server_smi:main',
          ],
          'gui_scripts': [
              'client_smi_gui = multiple_smi.client_smi_appindicator:main',
          ]
      },
      data_files=[('/etc/systemd/system', ['server_smi.service'])],
      install_requires=[
          'nvidia-ml-py3',
      ]
      )
