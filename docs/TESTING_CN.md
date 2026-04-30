# 测试说明

## 1. 无硬件单元测试

项目提供 mock SPI/GPIO，可在非树莓派环境运行：

```bash
python -m unittest discover -s tests -v
```

覆盖点：

- 初始化命令顺序
- BUSY 超时逻辑
- 纯色填充输出
- demo buffer 重映射
- 图片转换结果长度与基础路径

## 2. 硬件验证建议

在树莓派进行：

1. 先执行 `tools/test_colors.py` 验证接线与颜色
2. 再执行 `tools/display_image.py --image test.jpg`
3. 最后执行多轮刷新测试，观察稳定性

## 3. 常见失败定位

- `TimeoutError`：BUSY 电平不符合预期或连线错误
- 刷新慢/异常：降低 SPI 速率并确认供电稳定
- 图像方向错：通过 `--rotate` 修正
