#!/usr/bin/env python3

import os
import re
import sys
import json
import platform
import shutil
import argparse
import subprocess
from random import randint

UNAME_OS_WINDOWS = 'Windows'
UNAME_OS_DARWIN = 'Darwin'
UNAME_OS_LINUX = 'Linux'
UNAME_OS_FREEBSD = 'BSD'  # ?

QEMU_ACCEL = {
    UNAME_OS_LINUX: 'kvm',
    UNAME_OS_DARWIN: 'hvf',
    UNAME_OS_WINDOWS: 'whpx'
}

QEMU_ARCH_ARM32 = 'arm'
QEMU_ARCH_ARM64 = 'aarch64'
QEMU_ARCH_X32 = 'i386'
QEMU_ARCH_X64 = 'x86_64'
QEMU_ARCH_RV32 = 'riscv32'
QEMU_ARCH_RV64 = 'riscv64'

arch_patterns = {
    r'arm?64': QEMU_ARCH_ARM64,
    r'aarch64': QEMU_ARCH_ARM64,
    r'x86?64': QEMU_ARCH_X64,
    r'amd64': QEMU_ARCH_X64,
    r'x64': QEMU_ARCH_X64,
    r'i[3456]86': QEMU_ARCH_X32,
    r'risc?v?64': QEMU_ARCH_RV64,
    r'risc?v?32': QEMU_ARCH_RV32
}


def match_arch(tag):
    tag = tag.lower()
    for pattern in arch_patterns:
        if re.match(pattern, tag):
            return arch_patterns[pattern]
    return ''


# TODO: keep up to date
codename_db = {
    'trusty':  '14.04',
    'xenial':  '16.04',
    'bionic':  '18.04',
    'focal':   '20.04',
    'jammy':   '22.04',
    'kinetic': '22.10'
}


# FIXME

class Host(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Host, cls).__new__(cls)
            uname = platform.uname()
            arch = match_arch(uname.machine)
            if arch == '':
                raise 'Host arch is not supported yet!'
            cls.arch = arch
            cls.os_name = uname.system
        return cls.instance

    @classmethod
    def get_accel(cls):
        if cls.os_name in QEMU_ACCEL:
            return QEMU_ACCEL[cls.os_name]

        return None

    @classmethod
    def locate_qemu(cls, qemu_bin):
        qemu_path = shutil.which(qemu_bin)
        if qemu_path is not None:
            return qemu_path

        qemu_search_path = []
        if cls.os_name == UNAME_OS_WINDOWS:
            qemu_search_path.append('C:/Program Files/qemu')
        else:
            qemu_search_path.append('/usr/local/bin')
        # TODO: add more possible path(s) here

        for qpath in qemu_search_path:
            qpath += '/' + qemu_bin
            if cls.os_name == UNAME_OS_WINDOWS:
                qpath += '.exe'
            if os.path.exists(qpath):
                qemu_path = qpath
                break

        # # FIXME
        # qp = pathlib.Path(qemu_path)
        # if qp.is_symlink():
        #     qp_target = os.readlink(qemu_path)
        #     if not qp_target.startswith('/'):
        #         qp_target = os.path.dirname(qemu_path) + '/' + qp_target
        #     qemu_path = os.path.abspath(qp_target)

        return qemu_path


class Guest:
    vm_home = os.path.expanduser('~') + '/maxemu'

    def __init__(self):
        self.name = None

        self.model = ''
        self.arch = ''
        self.os_name = ''
        self.os_version = ''

        self.iso = None
        self.efi_code = ''
        self.vars_src = ''

        self.emulator = ''

    def get_vm_path(self):
        if self.name is None:
            return None
        return f'{Guest.vm_home}/{self.name}'


def parse_iso(iso: str):
    # parse file name
    image_name = os.path.basename(iso)[:-4]
    guest_info = parse_image_name(image_name.lower())

    # parse ISO label
    # FIXME: use API instead of shell utility
    skip = False
    skip_list = ['kali', 'freebsd']
    for pattern in skip_list:
        if image_name.startswith(pattern):
            skip = True
            break

    if skip == False and shutil.which('blkid') is not None:
        blkid_cmd = f'blkid -s LABEL -o value "{iso}"'
        result = subprocess.Popen(
            blkid_cmd, shell=True, stdout=subprocess.PIPE).stdout
        label = result.read().decode().strip()
        if len(label) > 5:
            label_info = parse_image_name(label.lower())
            for i in range(len(guest_info)):
                if label_info[i] != '':
                    guest_info[i] = label_info[i]

    # TODO: parse image contents

    return guest_info


def parse_image_name(image_name: str):
    os_name = os_version = arch = ''

    # FIXME
    max = 0
    for sep in ['_', '-', None]:
        sep_list = image_name.split(sep=sep)
        if len(sep_list) > max:
            max = len(sep_list)
            tag_list = sep_list

    if re.match('^[a-zA-Z]', tag_list[0]):
        os_name = tag_list[0]

    for tag in tag_list:
        if re.match(r'^win\d+$', tag) is not None:
            os_name = UNAME_OS_WINDOWS
            os_version = tag[3:]  # FIXME
        elif re.match(r'^windows$', tag) is not None:
            os_name = UNAME_OS_WINDOWS
        elif re.match(r'^[\d.]+$', tag) is not None or re.match(r'^[\d.]+_', tag) is not None:
            if os_version == '':
                os_version = tag
        elif tag in codename_db:
            os_name = 'ubuntu'
            os_version = codename_db[tag]
        else:
            for pattern in arch_patterns:
                if re.match(pattern, tag):
                    arch = arch_patterns[pattern]

    return [os_name, os_version, arch]


def create_vm(host: Host, guest: Guest):
    guest_path = guest.get_vm_path()
    if not os.path.exists(guest_path):
        os.makedirs(guest_path)

    # os.chdir(guest_path)

    shutil.copyfile('launch.py', guest_path + '/launch.py')

    qemu_config = []

    qemu_config.append(f'"{guest.emulator}"')

    qemu_config.append('-nodefaults')

    qemu_config.append('-machine ' + guest.model)

    if guest.arch == host.arch:
        hv = host.get_accel()
        if hv is not None:
            qemu_config.append('-accel ' + hv)
            if host.os_name != UNAME_OS_WINDOWS: # right?
                qemu_config.append('-cpu host')
        else:
            qemu_config.append('-cpu max')  # FIXME

    # FIXME
    qemu_config.append('-smp 4')
    qemu_config.append('-m 4G')

    # walkaround for hyper-v issue
    if host.os_name != UNAME_OS_WINDOWS or host.arch != guest.arch:
        locate_efi(host, guest)
        shutil.copyfile(guest.vars_src, guest_path + '/nvram.fd')
        qemu_config.append(
            f'-drive if=pflash,unit=0,format=raw,file={guest.efi_code},readonly=on')
        qemu_config.append(f'-drive if=pflash,unit=1,format=raw,file=nvram.fd')

    if guest.iso is not None:
        sys_disk = 'disk.qcow2'
        qemu_img = os.path.dirname(guest.emulator) + '/qemu-img'
        subprocess.run(
            f'"{qemu_img}" create -f qcow2 {guest_path}/{sys_disk} 40G', shell=True)

        # FIXME
        cdrom_bus = 'scsi'
        disk_bus = 'virtio'

        if 'scsi' in [cdrom_bus, disk_bus]:
            qemu_config.append('-device virtio-scsi-pci,id=scsi')
            scsi_id = 0

        if disk_bus == 'scsi':
            qemu_config.append(
                f'-device scsi-hd,bus=scsi.0,channel=0,scsi-id={scsi_id},drive=hd0')
            scsi_id += 1
        else:
            qemu_config.append('-device virtio-blk-pci,drive=hd0')

        if cdrom_bus == 'scsi':
            qemu_config.append(
                f'-device scsi-cd,bus=scsi.0,channel=0,scsi-id={scsi_id},drive=cd0')
            scsi_id += 1
        else:
            qemu_config.append('-device virtio-blk-pci,drive=cd0')

        qemu_config.append(
            '-drive if=none,id=cd0,media=cdrom,file=' + guest.iso)
        qemu_config.append(
            '-drive if=none,id=hd0,media=disk,file=' + sys_disk)

    qemu_config.append('-device qemu-xhci,id=usb-bus')
    qemu_config.append('-device usb-kbd,bus=usb-bus.0')
    qemu_config.append('-device usb-tablet,bus=usb-bus.0')

    mac = '52:54:' + ':'.join([f'{randint(2,253):02x}' for _ in range(4)])
    qemu_config.append(f'-device virtio-net-pci,mac={mac},netdev=nic0')
    qemu_config.append('-netdev user,id=nic0')

    qemu_config.append('-device intel-hda')
    qemu_config.append('-device hda-duplex')

    qemu_config.append('-device virtio-gpu-pci')
    if host.os_name == UNAME_OS_DARWIN:
        qemu_config.append('-display cocoa,show-cursor=on')

    with open(guest_path + '/vm.cfg', 'w') as cfg_fd:
        cfg_fd.write('\n'.join(qemu_config))


def locate_efi(host: Host, guest: Guest):
    qemu_dir = os.path.dirname(guest.emulator)
    if host.os_name == UNAME_OS_WINDOWS:
        firmware_dir = qemu_dir + '/share/firmware'
    else:
        firmware_dir = os.path.dirname(qemu_dir) + '/share/qemu/firmware'

    pattern = r'\d+-edk2-' + guest.arch
    if guest.os_name == UNAME_OS_WINDOWS and guest.os_version.isdigit() and int(guest.os_version) >= 10:
        pattern += '-secure.json'  # for Windows 10+ only
    else:
        pattern += '.json'

    json_path = None
    for fn in os.listdir(firmware_dir):
        if re.match(pattern, fn):
            json_path = firmware_dir + '/' + fn
            break

    if json_path is None:
        print('firmware not found!')
        exit(1)

    firmware_map = json.load(open(json_path))['mapping']
    guest.efi_code = firmware_map['executable']['filename']
    guest.vars_src = firmware_map['nvram-template']['filename']
    if host.os_name == UNAME_OS_WINDOWS:
        guest.efi_code = os.path.dirname(qemu_dir) + guest.efi_code
        guest.vars_src = os.path.dirname(qemu_dir) + guest.vars_src


def install():
    host = Host()

    guest = Guest()
    # if not os.path.exists(vm_home):
    #     os.makedirs(vm_home)

    parser = argparse.ArgumentParser()
    parser.add_argument('--cdrom', dest='iso',
                        default=None, help='/path/to/iso')
    args = parser.parse_args()

    if args.iso is None:
        guest.arch = host.arch
        guest.name = 'baremetal-' + guest.arch
    else:
        iso_path = args.iso
        result = parse_iso(iso_path)
        if '' in result:
            print('Invalid ISO image: ' + args.iso)
            exit(1)
        guest.iso = iso_path
        [guest.os_name, guest.os_version, guest.arch] = result

    if guest.model == '':
        if guest.arch == QEMU_ARCH_X64 or guest.arch == QEMU_ARCH_X32:
            guest.model = 'q35'
        else:
            guest.model = 'virt'

    #
    if guest.name is None:
        vm_name = f'{guest.os_name}-{guest.os_version}'
        if guest.arch != host.arch:
            vm_name += '-' + guest.arch

        if not os.path.exists(f'{Guest.vm_home}/{vm_name}'):
            guest.name = vm_name
        else:
            i = 1
            while True:
                new_name = f'{vm_name}-node{i}'
                if not os.path.exists(f'{Guest.vm_home}/{new_name}'):
                    guest.name = new_name
                    break
                i += 1

    qemu_bin = 'qemu-system-' + guest.arch
    guest.emulator = host.locate_qemu(qemu_bin)
    if guest.emulator is None:
        print(qemu_bin + ' not found, pls install it first!')
        exit(1)

    create_vm(host, guest)
    subprocess.call(f'python3 {guest.get_vm_path()}/launch.py', shell=True)
