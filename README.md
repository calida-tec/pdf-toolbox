# PDF Toolbox

一个轻量的 PDF 工具箱，包含：

- PDF 合并
- 多图片转 PDF
- 命令行版和桌面图形界面版

底层基于 Python、`pypdf` 和 `Pillow`。

## 安装

```powershell
cd PDF合并工具
python -m pip install -r requirements.txt
```

## 用法

### 图形界面版

直接启动：

```powershell
python .\pdf_merge_gui.py
```

或者双击：

```text
start_gui.bat
```

桌面启动器也仍然可用。

### 命令行版

合并 PDF：

```powershell
python .\pdf_merge_tool.py .\a.pdf .\b.pdf -o .\merged.pdf
```

图片转 PDF：

```powershell
python .\image_to_pdf_tool.py .\01.jpg .\02.png -o .\images.pdf
```

从目录批量导入图片：

```powershell
python .\image_to_pdf_tool.py -d .\photos -o .\album.pdf --recursive --overwrite
```

## 支持格式

图片转 PDF 支持这些格式：

- `.bmp`
- `.gif`
- `.jpeg`
- `.jpg`
- `.png`
- `.tif`
- `.tiff`
- `.webp`

## 说明

- 图形界面版使用 Python 自带的 `tkinter`
- 如果输出文件已存在，可勾选覆盖或使用 `--overwrite`
- 工具会自动按你在列表中的顺序生成 PDF
- 带透明通道的图片会自动铺白底，避免导出后出现黑底
