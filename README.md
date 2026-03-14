# autoBackgroundCut

一个本地图像处理工具：从输入文件夹中读取图片，检测人物、抠出人物并输出透明背景 PNG，同时保持原始分辨率与人物在图中的相对位置不变。

## 功能

- 支持常见图片格式：`jpg/jpeg/png/bmp/webp/tif/tiff`
- YOLO 人体检测（默认 `yolov8n`）
- rembg 抠图生成透明背景
- 输出始终保持原图尺寸（例如 `1024x1024`）
- UI 支持：
  - 输入文件夹选择
  - 输出文件夹选择
  - 随机抽取开关 + 数量设置
  - Python 环境候选展示
  - 开始处理按钮与进度显示
- 一键 `bat` 启动（Windows）

## 文件说明

- `ui.py`：Tkinter 图形界面
- `processor.py`：检测、抠图、输出逻辑
- `start_tool.bat`：Windows 一键启动脚本
- `requirements.txt`：依赖列表

## 使用方法

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 启动：

- Windows：双击 `start_tool.bat`
- 或命令行：

```bash
python ui.py
```

3. 在 UI 中选择输入/输出目录，按需开启随机抽取并设置数量，点击“开始处理”。

## 注意事项

- 首次运行 `ultralytics` 可能会下载模型文件（`yolov8n.pt`）。
- 若某张图片未检测到人物，会计入“跳过”。
- 若依赖未安装，处理会失败，请先安装 `requirements.txt`。
