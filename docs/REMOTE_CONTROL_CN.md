# 远程控制部署说明（Pi Server + Mac Hub）

本文档说明如何在同一 Wi-Fi 下，通过 Mac 控制 Pi Zero W 上的 GDEY0154F51 水墨屏。

## 1. 架构

- Pi Server（树莓派）：负责队列调度、鉴权、调用驱动刷新屏幕。
- Mac Hub（Mac）：负责内容渲染（image/text/todo）并转发到 Pi Server。
- 外部系统：调用 Mac Hub 的 REST API 触发显示。

## 2. Pi Server

### 2.1 环境变量

```bash
export API_KEY='replace-with-strong-key'
export BIND_HOST='0.0.0.0'
export PORT='8765'
export QUEUE_MAX_SIZE='100'

# 可选，覆盖 SPI / GPIO
export SPI_BUS='0'
export SPI_DEVICE='0'
export SPI_SPEED='2000000'
export SPI_MODE='0'
export PIN_RST='17'
export PIN_DC='25'
export PIN_CS='8'
export PIN_BUSY='24'
```

### 2.2 启动

```bash
python -m gdey0154f51.pi_server.main
```

### 2.3 systemd 开机自启示例

保存为 `/etc/systemd/system/gdey0154f51-pi-server.service`：

```ini
[Unit]
Description=GDEY0154F51 Pi Display Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/GDEY0154F51
Environment=API_KEY=replace-with-strong-key
Environment=BIND_HOST=0.0.0.0
Environment=PORT=8765
Environment=QUEUE_MAX_SIZE=100
ExecStart=/usr/bin/python3 -m gdey0154f51.pi_server.main
Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable gdey0154f51-pi-server
sudo systemctl start gdey0154f51-pi-server
sudo systemctl status gdey0154f51-pi-server
```

## 3. Mac Hub

### 3.1 `.env` 示例

```bash
export PI_BASE_URL='http://<pi-ip>:8765'
export PI_API_KEY='replace-with-strong-key'
export HUB_BIND_HOST='127.0.0.1'
export HUB_PORT='8780'
export PREFER_NATIVE_BUFFER='true'
```

### 3.2 启动

```bash
python -m gdey0154f51.mac_hub.main
```

## 4. 局域网端口与防火墙

- Pi 端需开放 TCP `8765` 给 Mac。
- Mac 若要被其他设备调用 Hub，需开放 TCP `8780`。
- 首版仅建议在可信局域网中使用，不建议直接暴露公网。

## 5. API 摘要

### 5.1 Pi Server

- `GET /v1/health`
- `GET /v1/capabilities`
- `POST /v1/jobs/display`（需要 `X-API-Key`）
- `GET /v1/jobs/{job_id}`（需要 `X-API-Key`）

`POST /v1/jobs/display` body:

- `payload_format`: `image_base64` 或 `native_buffer_base64`
- `payload_data`: base64 内容
- `content_meta`: `{mime_type, source, client_job_id}`（可选）
- `display_options`: `{dither, fit, rotate, auto_sleep}`

### 5.2 Mac Hub

- `POST /api/v1/display/image`
- `POST /api/v1/display/text`
- `POST /api/v1/display/todo`
- `GET /api/v1/jobs/{job_id}`

Mac Hub 会生成自身 `job_id`，并映射到 Pi 的 `pi_job_id`。
