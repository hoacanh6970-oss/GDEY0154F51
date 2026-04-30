# API 文档（中文）

## 主要类

### `GDEY0154F51`

高层 API，封装了完整显示流程。

常用构造：

- `GDEY0154F51.from_rpi(pin_config=None, spi_config=None, busy_timeout_s=20.0)`

常用方法：

- `display_image(image_path, dither=True, fit='contain', rotate=0, auto_sleep=True)`
- `display_native_buffer(buffer, auto_sleep=True)`
- `display_demo_buffer(buffer, auto_sleep=True)`
- `fill(color, auto_sleep=True)`
- `clear(auto_sleep=True)`
- `close()`

### `ImageConverter`

负责将普通图片转换为驱动 native buffer。

常用方法：

- `convert_file(image_path, options=None) -> bytes`
- `convert_image(pil_image, options=None) -> bytes`
- `buffer_to_preview(buffer) -> PIL.Image`

### `PinConfig`

默认引脚：`rst=17, dc=25, cs=8, busy=24`

### `SpiConfig`

默认 SPI：`bus=0, device=0, max_speed_hz=2000000, mode=0`

## 示例：显示一张图

```python
from gdey0154f51 import GDEY0154F51

with GDEY0154F51.from_rpi() as epd:
    epd.display_image("test.png", dither=True, fit="contain", rotate=0)
```

## 示例：纯色填充

```python
from gdey0154f51 import Color, GDEY0154F51

with GDEY0154F51.from_rpi() as epd:
    epd.fill(Color.YELLOW)
```

## demo buffer 兼容说明

Arduino 示例图像数据使用颜色顺序：

- `0=white`
- `1=yellow`
- `2=red`
- `3=black`

如果你直接使用示例数组，可调用 `display_demo_buffer`，驱动会自动重映射到 native 顺序。
