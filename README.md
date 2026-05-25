# 语声 — 跨平台语音输入法

**语声** 是一款跨平台语音输入工具，将语音实时转换为文字，帮助用户提高文本输入效率。支持在线（百度高精度 API）和离线（Whisper 本地模型）两种识别模式。

## 功能特性

- **双引擎识别**：百度 pro_api 高精度在线识别 + faster-whisper medium 离线识别，自动择优切换
- **实时转写**：停顿检测自动分段，边说边出字，支持最长 3 分钟连续语音
- **智能音频处理**：librosa 高质量重采样、高通滤波、noisereduce 降噪、峰值归一化
- **跨平台**：基于 Flutter + Python，支持 Windows / Mac / Linux
- **离线可用**：无需网络即可使用本地 Whisper 模型（faster-whisper medium int8）
- **简繁可选**：输出文字支持简体中文 / 繁體中文切换
- **主题切换**：浅色 / 深色 / 跟随系统三种主题模式
- **个性化设置**：语言、输出文字、API 密钥、服务器连接等可视化配置

## 技术架构

```
┌─────────────────────────┐
│   Flutter UI (Dart)     │  ← 用户界面、实时音量、文字展示
├─────────────────────────┤
│   WebSocket (ws:8765)   │  ← 前后端通信
├─────────────────────────┤
│   Python Core           │  ← 音频采集、预处理、识别调度
│   ├── AudioCapture      │  ← PyAudio 实时采集
│   ├── AudioPipeline     │  ← librosa/scipy/noisereduce 预处理
│   ├── BaiduASR (在线)    │  ← 百度 pro_api (dev_pid 80001)
│   └── WhisperASR (离线)  │  ← faster-whisper medium int8
└─────────────────────────┘
```

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥3.10 | 核心服务运行环境 |
| Flutter | ≥3.10 | UI 框架 |
| PyAudio | 0.2.14 | 音频采集 |
| faster-whisper | 1.2+ | 离线识别引擎（CTranslate2 后端）|
| scipy | 1.17+ | 信号处理 |
| librosa | 0.10+ | 高质量音频重采样 |
| noisereduce | — | 背景降噪 |
| zhconv | 1.4+ | 简繁中文转换 |

## 快速开始

### 1. 安装依赖

```bash
pip install pyaudio faster-whisper scipy librosa noisereduce zhconv numpy websockets requests
```

### 2. 启动 Python 服务端

```bash
cd src/python_core
python server.py
```

首次启动会自动检测麦克风并下载 Whisper 模型（约 500MB）。

### 3. 启动 Flutter 客户端

```bash
cd src/flutter_app
flutter run -d windows
```

### 4. 配置百度 API（可选，推荐）

在应用「设置」页面填入百度语音识别 API Key 和 Secret Key，开启在线高精度识别。
免费额度 5 万次/月，申请地址：https://ai.baidu.com/tech/speech

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `YUSHENG_HOST` | 服务端绑定地址 | `127.0.0.1` |
| `YUSHENG_PORT` | 服务端端口 | `8765` |
| `YUSHENG_API_KEY` | 百度 API Key | — |
| `YUSHENG_SECRET_KEY` | 百度 Secret Key | — |
| `YUSHENG_DEVICE` | 指定麦克风设备索引 | 自动检测 |

## 项目结构

```
voice-input-method/
├── src/
│   ├── flutter_app/           # Flutter 前端
│   │   └── lib/
│   │       ├── main.dart
│   │       ├── pages/
│   │       │   ├── home_page.dart        # 主页面（录音+文字显示）
│   │       │   ├── settings_page.dart    # 设置页面
│   │       │   └── mic_test_page.dart    # 麦克风诊断
│   │       └── services/
│   │           ├── voice_service.dart     # 语音服务（WebSocket 通信）
│   │           └── theme_service.dart     # 主题管理
│   └── python_core/           # Python 后端
│       ├── server.py                     # WebSocket 服务入口
│       ├── audio/
│       │   └── capture.py                # PyAudio 音频采集
│       └── recognition/
│           ├── baidu_asr.py              # 百度在线识别
│           └── whisper_asr.py            # 本地离线识别
├── docs/                      # 项目文档
│   ├── requirements.md
│   ├── technical-design.md
│   ├── design-spec.md
│   └── api-reference.md
└── dev-logs/                  # 开发日志
```

## 使用方式

1. 点击麦克风按钮开始录音
2. 对着麦克风说话，文字实时显示在下方区域
3. 停顿 1.5 秒自动分段识别
4. 再次点击麦克风停止录音
5. 点击「复制」将文字复制到剪贴板

## License

MIT
