from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='Multiple smi',
      version='2.0.3',
      url='https://github.com/ClementPinard/multiple-smi',
      license='MIT',
      author='Clément Pinard',
      author_email='clempinard@gmail.com',
      description='Look up GPU/CPU/RAM usage on multiple servers at the same time',
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'client_smi = multiple_smi.client.client_smi:main',
              'discover_hosts = multiple_smi.client.update_hosts_list:main',
              'server_smi = multiple_smi.server.server_smi:main',
              'install_server_service = multiple_smi.server.install_server_service:main'
          ]
      },
      install_requires=[
          'numpy',
          'python-nmap',
          'colorspacious',
          'py-cpuinfo',
          'pycairo',
          'nvidia-ml-py3',
          'pyzmq',
          'psutil'
      ],
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Science/Research"
      ]
      )
