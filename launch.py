#!/usr/bin/env python3

import os
import sys
import subprocess


def launch_vm():
    config = []
    with open('vm.cfg', 'r') as cfg_fd:
        for line in cfg_fd:
            config.append(line.strip())

    subprocess.run(' '.join(config), shell=True)


if __name__ == '__main__':
    dir = os.path.dirname(sys.argv[0])
    if dir != '' and dir != './':
        os.chdir(dir)
    launch_vm()