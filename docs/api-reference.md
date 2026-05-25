# 语声 - API参考文档

## 百度语音识别API

### 接口信息

| 项目 | 说明 |
|------|------|
| 接口地址 | https://vop.baidu.com/server_api |
| 认证方式 | Access Token (OAuth 2.0) |
| 音频格式 | PCM 16kHz 16bit 单声道 |
| 支持语言 | 中文普通话、粤语、四川话等 |
| 免费额度 | 5万次/月 |

### 认证流程

1. 获取Access Token
```
POST https://aip.baidubce.com/oauth/2.0/token
参数：grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}
```

2. 语音识别请求
```
POST https://vop.baidu.com/server_api
参数：
  - dev_pid: 语言模型ID（1537=普通话）
  - format: pcm
  - rate: 16000
  - channel: 1
  - token: Access Token
  - cuid: 用户标识
  - speech: Base64编码音频数据
  - len: 原始音频字节数
```

### 常用dev_pid

| dev_pid | 语言 | 说明 |
|---------|------|------|
| 1537 | 普通话 | 通用模型 |
| 1536 | 普通话 | 搜索模型 |
| 1737 | 英语 | 英语识别 |
| 1637 | 粤语 | 粤语识别 |
| 1837 | 四川话 | 四川话识别 |

## Whisper本地模型

### 模型选择

| 模型 | 大小 | 内存需求 | 准确度 |
|------|------|----------|--------|
| tiny | 39MB | ~1GB | 基础 |
| base | 74MB | ~1GB | 中等 |
| small | 244MB | ~2GB | 较好 |
| medium | 769MB | ~5GB | 良好 |
| large | 1550MB | ~10GB | 最佳 |

### 使用方式

```python
import whisper

# 加载模型
model = whisper.load_model("base")

# 语音识别
result = model.transcribe("audio.wav")
print(result["text"])
```

## 内部API接口

### Python核心服务

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/recognize | POST | 语音识别（在线） |
| /api/recognize/offline | POST | 语音识别（离线） |
| /api/status | GET | 服务状态查询 |
| /api/settings | GET/POST | 设置管理 |
| /api/dictionary | GET/POST/PUT/DELETE | 词库管理 |

### gRPC服务定义

```protobuf
service VoiceInput {
  rpc Recognize(stream AudioChunk) returns (stream RecognitionResult);
  rpc GetStatus(Empty) returns (StatusResponse);
  rpc UpdateSettings(Settings) returns (Settings);
}
```
