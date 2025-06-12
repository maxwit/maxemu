# MaxEmu

## 介绍
MaxEmu是一个全平台虚拟机管理器（cross-platform virtual machine manager）。

前期用python辅助架构设计和技术验证，之后用Flutter或Kivy框架（待定）开发App。

## Quick Start

### Setup VM
```shell
python3 setup-vm.py --cdrom ~/Downloads/ubuntu-24.04.2-desktop-amd64.iso
```

### Launch VM
```shell
python3 ~/maxemu/ubuntu-24.04.2/launch.py
```

## 各VMM支持的软硬件平台

### Host平台

 |         |        MaxEmu         |       VMWare       |         PD         |     VirtualBox     |        UTM         |    Virt-manager    |
 | :-----: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: |
 | Windows | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |        :x:         |        :x:         |
 |  Linux  | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |        :x:         | :white_check_mark: |
 |  macOS  | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |        :x:         |
 |   iOS   | :white_check_mark: |        :x:         |        :x:         |        :x:         | :white_check_mark: |        :x:         |
 | Android | :white_check_mark: |        :x:         |        :x:         |        :x:         |        :x:         |        :x:         |


#### Guest平台

 |            |        MaxEmu         |       VMWare       |         PD         |     VirtualBox     |        UTM         |    Virt-manager    |
 | :--------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: |
 | 同构指令集 | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
 | 异构/交叉  | :white_check_mark: |        :x:         |        :x:         |        :x:         | :white_check_mark: | :white_check_mark: |
 |    RTOS    | :white_check_mark: |        :x:         |        :x:         |        :x:         |        :x:         |        :x:         |
 |    MCU     | :white_check_mark: |        :x:         |        :x:         |        :x:         |        :x:         |        :x:         |