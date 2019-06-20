#!/usr/bin/env python3.6

import configparser

config = configparser.ConfigParser()
config['VM_base'] = {'name': 'sandbox2',
                     'HD_size_MB': '32768',
                     'ostype': 'Ubuntu_64',
                     'iso_path': '/home/william/Downloads/ubuntu-18.04.2-desktop-amd64.iso'
                     }
config['DEFAULT']['base_dir'] = '/home/william/.vms'
with open('example.ini', 'w') as configfile:
    config.write(configfile)