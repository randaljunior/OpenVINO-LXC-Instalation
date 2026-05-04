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
## Repositórios e drivers
<details>
    <summary>Ubuntu</summary>
<p>
    
- Instalar as primeiras dependências
```
add-apt-repository universe -y
apt update && apt dist-upgrade -y
apt install -y software-properties-common gpg
```
- Repositórios da Intel
```
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null && \
echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | tee /etc/apt/sources.list.d/oneAPI.list
```
- Instalar drivers Intel
```
apt update && \
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

</p>
</details>

<details>
    <summary>Ubuntu</summary>
<p>

- Instalar as primeiras dependências
```
apt update && apt dist-upgrade -y
apt install -y gpg
```
- Repositórios da Intel
```
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null && \
echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | tee /etc/apt/sources.list.d/oneAPI.list
```
- Instalar drivers Intel
```
apt install ocl-icd-libopencl
```
- Procurar o runtime mais recente em https://github.com/intel/compute-runtime/releases e instalar.
</p>
</details>


## Corrigir erro de grupo de Hardware
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

## Instalação do Python
- Instalar o python3 e suas dependências:
```
apt install -y python3-full python3-venv python3-pip python3-dev build-essential git curl wget ca-certificates
python3 -m venv /opt/openvino-llm/venv
source /opt/openvino-llm/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install \
  openvino \
  openvino-genai \
  optimum-intel \
  "optimum[openvino]" \
  transformers \
  accelerate \
  sentence-transformers \
  fastapi \
  uvicorn \
  huggingface_hub \
  torch \
  compressed-tensors \
  pillow \
  requests \
  "numpy<2.0"
```

- Identificar se a GPU está acessível:
```
python3 - <<'PY'
import openvino as ov

core = ov.Core()
print("Dispositivos:", core.available_devices)

for device in core.available_devices:
    try:
        print(device, "-", core.get_property(device, "FULL_DEVICE_NAME"))
    except Exception as e:
        print(device, "-", e)
PY
```

## Instalando os modelos google/gemma-4-E2B-it e nomic-ai/nomic-embed-text-v1.5
```
optimum-cli export openvino \
  --model google/gemma-4-E2B-it \
  /models/openvino/gemma-4-E2B-it
```
```
optimum-cli export openvino \
  --model nomic-ai/nomic-embed-text-v1.5 \
  --task feature-extraction \
  --trust-remote-code \
  /models/openvino/nomic-embed-text-v1.5
```

## Executando o Servidor
### Servidor de modelos
```
cd /opt/openvino-llm
uvicorn server_llm:app --host 0.0.0.0 --port 8000
```
- Scripts de teste
```
curl http://127.0.0.1:8000/v1/models
```
```
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-4-E2B-it-openvino",
    "messages": [
      {"role": "user", "content": "Explique em uma frase o que é OpenVINO."}
    ],
    "max_tokens": 80
  }'
```

### Servidor de Embenddings
```
cd /opt/openvino-llm
uvicorn server_embed:app --host 0.0.0.0 --port 8001
```
- Scripts de teste
```
curl http://127.0.0.1:8001/v1/models
```
```
curl http://127.0.0.1:8001/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text-v1.5-openvino",
    "input": "Este é um teste de embedding local com OpenVINO."
  }'
```

### Criando um Serviço
- Verificando o caminho do aplicativo uvicorn
```
which uvicorn
```

- Criar o serviço de Chat: /etc/systemd/system/openvino-llm.service
```
[Unit]
Description=OpenVINO Gemma LLM OpenAI-compatible API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/openvino-llm
Environment="XDG_RUNTIME_DIR=/tmp"
ExecStart=/usr/local/bin/uvicorn server_llm:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- Criar o serviço de Embendding: /etc/systemd/system/openvino-embed.service
```
[Unit]
Description=OpenVINO Nomic Embedding OpenAI-compatible API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/openvino-llm
Environment="XDG_RUNTIME_DIR=/tmp"
ExecStart=/usr/local/bin/uvicorn server_embed:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- Ativar os serviços
```
systemctl daemon-reload
systemctl enable --now openvino-llm
systemctl enable --now openvino-embed
```




