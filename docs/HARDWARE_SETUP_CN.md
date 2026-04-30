# 硬件与系统配置

## 1. 接线

以下为默认 BCM 接线：

- 屏幕 `BUSY` -> GPIO24
- 屏幕 `RST` -> GPIO17
- 屏幕 `DC` -> GPIO25
- 屏幕 `CS` -> GPIO8 (SPI0 CE0)
- 屏幕 `SCLK` -> GPIO11 (SPI0 SCLK)
- 屏幕 `DIN` -> GPIO10 (SPI0 MOSI)
- `3.3V` 与 `GND` 按模块要求连接

## 2. 启用 SPI

```bash
sudo raspi-config
```

进入 `Interface Options` -> `SPI` -> `Enable`。

## 3. 权限

建议在 `pi` 用户下执行，并确保当前用户可访问 `/dev/spidev0.*`。

## 4. 时序说明

驱动对齐了 Arduino 示例中的关键时序：

- reset 前后延时：20ms / 40ms / 50ms
- BUSY 轮询：BUSY=1 视为空闲
- 每次全刷：`init -> write image -> refresh -> sleep`
- sleep 前电源关闭后保留 100ms

## 5. 常见问题

- BUSY 一直 0：检查 BUSY 引脚是否接反或供电不足
- 花屏：降低 SPI 速率（例如 `--spi-speed 1000000`）
- 颜色异常：先跑 `tools/test_colors.py` 校验硬件链路
