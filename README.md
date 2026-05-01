# GDEY0154F51 Raspberry Pi Driver

基于官方 Arduino 示例迁移的 Raspberry Pi Python 驱动，目标屏幕为 GDEY0154F51（152x152, 4-color, 2bpp）。

## 特性

- 使用 `spidev` 和 `RPi.GPIO`
- 面向对象驱动 API，适合二次开发
- 提供图像转换工具（普通图片 -> 墨水屏 native buffer）
- 提供无硬件单元测试和硬件示例脚本
- 文档为中文

## 目录

- `gdey0154f51/`：核心驱动和转换库
- `tools/`：命令行工具（转换、上屏、颜色测试）
- `examples/`：使用案例
- `tests/`：单元测试（不依赖硬件）
- `docs/`：详细文档

## 快速开始

### 1. 树莓派准备

启用 SPI：

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
```

安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 直接运行最小示例

```bash
python sample.py
```

### 3. 转换图片并显示

先转换：

```bash
python tools/convert_image.py \
  --input assets/test.jpg \
  --output-bin output.bin \
  --preview output_preview.png
```

再上屏：

```bash
sudo python tools/display_image.py --image assets/test.jpg
```

### 4. 四色测试

```bash
sudo python tools/test_colors.py --interval 2 --repeat 1
```

## 默认引脚

默认使用 BCM 编号：

- `RST=17`
- `DC=25`
- `CS=8`
- `BUSY=24`

可在工具命令行参数中覆盖。

## API 示例

```python
from gdey0154f51 import GDEY0154F51

with GDEY0154F51.from_rpi() as epd:
    epd.display_image("test.png", dither=True, fit="contain", auto_sleep=True)
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## Wi-Fi 远程控制（Pi Server + Mac Hub）

安装新增依赖后，可分别启动：

```bash
# Pi 端（建议在树莓派执行）
python -m gdey0154f51.pi_server.main

# Mac 端 Hub
python -m gdey0154f51.mac_hub.main
```

也可使用工具脚本：

```bash
python tools/run_pi_server.py
python tools/run_mac_hub.py
```

接口摘要：

- Pi Server：`/v1/health`, `/v1/capabilities`, `/v1/jobs/display`, `/v1/jobs/{job_id}`
- Mac Hub：`/api/v1/display/image`, `/api/v1/display/text`, `/api/v1/display/todo`, `/api/v1/jobs/{job_id}`

## 重要说明

- 该屏幕每次全刷建议走 `init -> display -> sleep`，本库默认遵循该流程。
- 刷新后建议进入 deep sleep，以保护屏幕寿命。
- `tools/display_image.py --no-sleep` 仅用于调试，不建议长期使用。

更多内容见：

- `docs/HARDWARE_SETUP_CN.md`
- `docs/API_CN.md`
- `docs/TOOLS_CN.md`
- `docs/TESTING_CN.md`
- `docs/REMOTE_CONTROL_CN.md`
