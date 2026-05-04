# 工具使用说明

## 1. 图片转换

脚本：`tools/convert_image.py`

示例：

```bash
python tools/convert_image.py \
  --input test.jpg \
  --output-bin out.bin \
  --preview out_preview.png \
  --fit contain
```

参数：

- `--input` 输入图片
- `--output-bin` 输出 native 二进制缓冲
- `--preview` 可选，输出预览图
- `--fit` `contain|cover|stretch`
- `--rotate` `0|90|180|270`
- `--no-dither` 关闭抖动

## 2. 直接上屏

脚本：`tools/display_image.py`

```bash
sudo python tools/display_image.py --image test.jpg
```

可选参数：

- `--spi-bus` `--spi-device` `--spi-speed`
- `--spi-backend hardware|software`
- `--soft-sck` `--soft-mosi`
- `--soft-bit-delay-us` `--soft-cs-gap-us`
- `--pin-rst` `--pin-dc` `--pin-cs` `--pin-busy`
- `--no-sleep` 调试用，不建议常用

软件 SPI 示例（稳定优先）：

```bash
sudo python tools/display_image.py \
  --image test.jpg \
  --spi-backend software \
  --soft-bit-delay-us 1 \
  --soft-cs-gap-us 10
```

## 3. 四色链路测试

脚本：`tools/test_colors.py`

```bash
sudo python tools/test_colors.py --interval 2 --repeat 2
```

会按顺序显示：Black -> White -> Yellow -> Red。
