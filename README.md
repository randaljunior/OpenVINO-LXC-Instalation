# Como instalar o OpenVINO do LXC do Proxmox
- Criar um LXC com a imagem Ubuntu 26.04
- Incluir os seguintes registros no /etc/pve/lxc/<ID>.conf:
  ```
  lxc.cgroup2.devices.allow: c 226:0 rwm
  lxc.cgroup2.devices.allow: c 226:128 rwm
  lxc.mount.entry: /dev/dri/card0 dev/dri/card0 none bind,optional,create=file
  lxc.mount.entry: /dev/dri/renderD128 dev/dri/renderD128 none bind,optional,create=file
  lxc.idmap: u 0 100000 65536
  lxc.idmap: g 0 100000 44
  lxc.idmap: g 44 44 1
  lxc.idmap: g 45 100045 59
  lxc.idmap: g 104 104 1
  lxc.idmap: g 105 100105 65431
  ```
