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
- `--pin-rst` `--pin-dc` `--pin-cs` `--pin-busy`
- `--no-sleep` 调试用，不建议常用

## 3. 四色链路测试

脚本：`tools/test_colors.py`

```bash
sudo python tools/test_colors.py --interval 2 --repeat 2
```

会按顺序显示：Black -> White -> Yellow -> Red。
