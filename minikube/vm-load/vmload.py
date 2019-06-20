#!/usr/bin/env python3.6

import configparser
import subprocess
import sys
from pathlib import Path

# Inspired by https://www.perkin.org.uk/posts/create-virtualbox-vm-from-the-command-line.html

def os_call(commandarray):
    result = subprocess.run(commandarray, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
#    print(result)
    if result.returncode != 0:
        subprocess.CalledProcessError('failed executing:'+str(result))
    return result.stdout


def list_vms():
    result = os_call(['VBoxManage', 'list', '-s', 'vms'])
    return [line.split('"')[1] for line in result.split('\n') if line != '']


def check_vm_not_present(list, name):
    if name is None or name == '':
        raise ValueError('Name must not be empty')
    if name in list:
        print(f"VM name '{name}' already in virtualbox. Please move/delete before choosing to rerun this script.")
        sys.exit(1)

def derive_dynamic_disc_path(directory, name):
    return Path(directory).joinpath(name+"/"+name+'.vdi')

def check_dynamic_disc_not_present(path):
    if path.exists():
        raise ValueError(f"Dynamic disc already present at'{path}', please delete before deciding to rerun this script")

def create_dynamic_disc(path, size):
    path.parent.mkdir(parents=True, exist_ok=True)
    if size < 10*1000:
        raise ValueError("disc size is in Mb and must be greater than 10k")
    return os_call(['VBoxManage', 'createhd', '--filename', str(path), '--size', str(size)])

def get_allowed_ostypes():
    raw_list = os_call(['VBoxManage', 'list', 'ostypes'])
    return [line.split('          ')[1] for line in raw_list.split('\n') if line.startswith('ID')]

def check_ostype_is_allowed(allowed_ostypes, ostype):
    if ostype is None or ostype == "":
        raise ValueError(f"Ostype must be chosen, use ID values from 'VBoxManage list ostypes'")
    if ostype not in allowed_ostypes:
        raise ValueError(f"ostype must be one of the values from 'VBoxManage list ostypes'")

def create_vm(name, ostype):
    return os_call(['VBoxManage', 'createvm', '--name', name, '--ostype', ostype, '--register'])

def add_sata_controller(name):
    return os_call(['VBoxManage', 'storagectl', name, '--name', 'SATA Controller', '--add', 'sata', '--controller', 'IntelAHCI'])

def attach_dynamic_disc(name, path):
    return os_call(['VBoxManage', 'storageattach', name, '--storagectl', 'SATA Controller', '--port', '0', '--device',
                    '0', '--type', 'hdd', '--medium', path])

def add_ide_controller(name):
    return os_call(['VBoxManage', 'storagectl', boxname, '--name', 'IDE Controller', '--add', 'ide'])

def attach_iso_to_ide(name, path):
    return os_call(['VBoxManage', 'storageattach', boxname, '--storagectl', 'IDE Controller', '--port', '0',
                    '--device', '0', '--type', 'dvddrive', '--medium', path])

def check_iso_is_present(path):
    if path is None or path == "":
        raise ValueError(f"the iso path must be present a point to a valid file")
    if not path.exists():
        raise ValueError(f"path '{path}' does not refer to a valid file")

def modifyvm(name, commandarray):
    return os_call(['VBoxManage', 'modifyvm', name]+commandarray)

def unattended_install(name, commandarray):
    return os_call(['VBoxManage', 'unattended', 'install', name]+commandarray)


if __name__ == '__main__':
    print ("Placing Sandbox definition in virtualbox\n")
    config = configparser.ConfigParser()
    settings = config.read('example.ini')
    boxname = config['VM_base']['name']
    check_vm_not_present(list_vms(), boxname)

    # Create dynamic disc
    path = derive_dynamic_disc_path(config['DEFAULT']['base_dir'], boxname)
    check_dynamic_disc_not_present(path)
    create_dynamic_disc(path, int(config['VM_base']['hd_size_mb']))

    # check os type
    ostype = config['VM_base']['ostype']
    check_ostype_is_allowed(get_allowed_ostypes(), ostype)

    # create VM
    create_vm(boxname, ostype)
    add_sata_controller(boxname)
    attach_dynamic_disc(boxname, path)
    isopath = Path(config['VM_base']['iso_path'])
    check_iso_is_present(isopath)
    add_ide_controller(boxname)
    attach_iso_to_ide(boxname, isopath)

    # modify settings
    modifyvm(boxname, ['--ioapic', 'on'])
    modifyvm(boxname, ['--memory', '6100', '--vram', '128'])
    modifyvm(boxname, ['--boot1', 'dvd', '--boot2', 'disk', '--boot3', 'none', '--boot4', 'none'])

    print("Setup successful, now starting vm install using virtualbox\n")

    #first a hack workaround
 #   os_call(['rm', '/usr/share/virtualbox/UnattendedTemplates'])
  #  os_call(['ln', '-s', '/usr/lib/virtualbox/UnattendedTemplates/', 'UnattendedTemplates'])


    unattended_install(boxname, ['--iso', isopath, '--user', 'william', '--password', 'stdiN', '--country', 'GB', '--time-zone', 'UTC', '--start-vm', 'gui'])
