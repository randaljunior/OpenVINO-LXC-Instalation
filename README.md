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

# Repositórios e drivers
- Repositórios da Intel
```
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null && \
echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | sudo tee /etc/apt/sources.list.d/oneAPI.list
```
- Instalar as primeiras dependências
```
add-apt-repository universe -y
apt update && apt dist-upgrade -y
apt install -y software-properties-common
```
- Instalar drivers Intel
```
apt install -y \
intel-opencl-icd \
intel-media-va-driver-non-free \
intel-oneapi-runtime-opencl \
intel-oneapi-runtime-dpcpp-sycl-opencl-cpu \
intel-oneapi-runtime-openmp-opencl-shared \
intel-gpu-tools \
intel-ocloc \
libigc-tools \
libigc2-tools \
libigdfcl1 \
libigdfcl2 \
libmfx-gen1.2 \
libze-intel-gpu-raytracing \
libze-intel-gpu1 \
libze1 \
vainfo \
clinfo
```

# Corrigir erro de grupo de Hardware
- Executar os seguintes comandos e fazer um reboot:
```
groupmod -n render-old render && \
groupmod -n render postdrop && \
usermod -aG render root && \
dpkg-statoverride --remove /usr/sbin/postqueue && \
dpkg-statoverride --remove /usr/sbin/postdrop && \
apt install -f
```
- Testar com os seguintes comandos:
```
ls -l /dev/dri
grep '^render:' /etc/group
id
lspci -nn | grep -Ei 'vga|3d|display'
vainfo --display drm --device /dev/dri/renderD128
clinfo | head -120
```
Deve aparecer algo como o texto abaixo e identificar corretamente a GPU
```
crw-rw---- 1 nobody video  226,   0 May  3 20:58 card0
crw-rw---- 1 nobody render 226, 128 Apr 27 20:48 renderD128

render:x:104:root

uid=0(root) gid=0(root) groups=0(root),104(render)
```



