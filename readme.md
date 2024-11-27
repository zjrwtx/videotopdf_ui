# 视频转PDF智能助手
使用地址：https://zjrwtxtechstudio-video-to-pdf.hf.space

这是一个基于 Gradio 的 Web 应用，可以将视频自动转换为 PDF 文档。应用会智能检测视频中的关键帧，并将其转换为高质量的 PDF 文件。同时支持视频语音转写功能，可以将视频中的语音内容自动转换为文字。
![image](https://github.com/user-attachments/assets/e6b797b0-1893-44aa-a70d-22f9052f0268)



## 功能特点

- 智能检测视频关键帧
- 自动生成高质量PDF
- 支持多种视频格式（mp4, avi, mov等）
- 语音转写功能（基于OpenAI Whisper）
- 简单易用的Web界面
- 支持进度显示

## 安装说明

1. 克隆项目到本地
```bash
git clone [项目地址]
cd videotopdf_ui
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 基础视频转PDF功能
1. 上传视频文件或输入视频路径
2. 点击"开始转换"按钮
3. 等待处理完成后下载生成的PDF

### 带语音转写的视频转PDF功能
1. 上传视频文件
2. 选择"包含语音转写"选项
3. 点击"开始转换"按钮
4. 系统会自动提取视频中的语音并转换为文字
5. 生成的PDF将包含视频画面和对应的文字内容

## 技术栈

- Python
- OpenCV：视频处理和帧提取
- Gradio：Web界面框架
- scikit-image：图像处理
- img2pdf：PDF生成
- OpenAI Whisper：语音识别转写
- moviepy：音频提取

## 系统要求

- Python 3.8+
- 足够的磁盘空间用于临时文件存储
- 建议有GPU支持（用于加速语音识别）

## 注意事项

- 处理大型视频文件时可能需要较长时间
- 语音转写功能需要下载Whisper模型，首次使用时会自动下载
- 确保有足够的磁盘空间存储临时文件

## 许可证 仅供学习交流 不可商用
