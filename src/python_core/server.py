"""
语声 - Python核心服务
通过 WebSocket 提供语音识别服务给 Flutter 前端
"""

import asyncio
import json
import threading
import numpy as np
from websockets.asyncio.server import serve

from audio.capture import AudioCapture
from recognition.baidu_asr import BaiduASR
from recognition.whisper_asr import recognize as whisper_recognize
from recognition.whisper_asr import check_available as whisper_available
from recognition.whisper_asr import load_model as whisper_load_model
from command.parser import parse as parse_command


TARGET_RATE = 16000


def _preprocess_audio(audio_bytes: bytes, orig_rate: int, target_rate: int = TARGET_RATE) -> bytes:
    """完整的音频预处理管道：重采样 → 高通滤波 → 降噪 → 归一化"""
    audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

    # 1. 高质量重采样（librosa 的 Kaiser 窗 sinc 插值，比 scipy 好）
    if orig_rate != target_rate:
        import librosa
        audio = librosa.resample(audio, orig_sr=orig_rate, target_sr=target_rate)

    # 2. 高通滤波：去除 80Hz 以下的低频噪音（风声、机械振动、空调嗡声）
    try:
        from scipy.signal import butter, filtfilt
        nyq = target_rate / 2
        b, a = butter(4, 80 / nyq, btype='high')
        audio = filtfilt(b, a, audio)
    except Exception:
        pass

    # 3. 降噪：消除稳态背景噪音（风扇、电流声等）
    try:
        import noisereduce as nr
        audio = nr.reduce_noise(y=audio, sr=target_rate, prop_decrease=0.8)
    except Exception:
        pass

    # 4. 峰值归一化到 90% 动态范围
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.9

    return (audio * 32767).astype(np.int16).tobytes()


def _resample(audio_bytes: bytes, orig_rate: int, target_rate: int = TARGET_RATE) -> bytes:
    """将音频重采样到目标采样率"""
    if orig_rate == target_rate:
        return audio_bytes
    from scipy.signal import resample_poly
    import fractions
    ratio = fractions.Fraction(target_rate, orig_rate)
    audio = np.frombuffer(audio_bytes, dtype=np.int16)
    resampled = resample_poly(audio.astype(np.float64), ratio.numerator, ratio.denominator)
    np.clip(resampled, -32768, 32767, out=resampled)
    return resampled.astype(np.int16).tobytes()


class VoiceServer:
    def __init__(self, api_key: str = "", secret_key: str = "", device_index: int = None, sample_rate: int = 16000):
        self.capture = AudioCapture(device_index=device_index, sample_rate=sample_rate)
        self.baidu = BaiduASR(api_key=api_key, secret_key=secret_key)
        self.online_available = True
        self.language = "zh-CN"
        self.script = "simplified"
        self._clients = set()
        self._running = False
        self._task = None
        self._model_ready = False

    def _ensure_model(self):
        """延迟加载 Whisper 模型（首次使用时加载）"""
        if not self._model_ready:
            try:
                whisper_load_model()
                self._model_ready = True
            except Exception as e:
                raise RuntimeError(f"离线模型加载失败: {e}")

    async def start(self, host="127.0.0.1", port=8765):
        self._running = True
        async with serve(self._handle_client, host, port) as server:
            print(f"语声服务已启动: ws://{host}:{port}")
            await asyncio.get_running_loop().create_future()  # run forever

    async def _handle_client(self, websocket):
        self._clients.add(websocket)
        try:
            async for message in websocket:
                await self._dispatch(websocket, message)
        finally:
            self._clients.discard(websocket)

    async def _dispatch(self, ws, raw: str):
        try:
            msg = json.loads(raw)
            cmd = msg.get("command", "")
        except json.JSONDecodeError:
            return

        match cmd:
            case "start_recognition":
                await self._start_recognition(ws, msg)
            case "stop_recognition":
                self._stop_recognition()
                await ws.send(json.dumps({"event": "stopped"}))
            case "get_status":
                await ws.send(json.dumps(self._get_status()))
            case "update_settings":
                await self._update_settings(msg)
            case _:
                await ws.send(json.dumps({"event": "error", "data": f"未知命令: {cmd}"}))

    async def _start_recognition(self, ws, msg: dict):
        lang = msg.get("language", "zh-CN")
        prefer_online = msg.get("online", True)
        script = msg.get("script", "simplified")

        self.language = lang
        self.script = script
        self.capture.start()

        self._task = asyncio.create_task(self._recognition_loop(ws, prefer_online))

    async def _recognition_loop(self, ws, prefer_online: bool):
        try:
            speech_buffer = b""  # 当前段落累积的语音
            silence_frames = 0    # 连续静音帧计数
            segment_index = 0     # 段落序号
            while self.capture._running:
                chunk = self.capture.read_all()
                if chunk:
                    speech_buffer += chunk

                level = self.capture.get_audio_level()
                await ws.send(json.dumps({
                    "event": "audio_level",
                    "data": {"level": level}
                }))

                bytes_per_second = self.capture.sample_rate * 2
                buffer_seconds = len(speech_buffer) / bytes_per_second if bytes_per_second else 0

                # 停顿检测：音量持续低于阈值 = 用户说完一段
                SILENCE_THRESHOLD = 0.02
                SILENCE_DURATION = 1.5  # 1.5秒停顿认为是段落结束
                if level < SILENCE_THRESHOLD:
                    silence_frames += 1
                else:
                    silence_frames = 0

                silence_sec = silence_frames * 0.1  # 每帧0.1秒
                min_speech_sec = 2.0  # 至少2秒有效语音

                should_send = False
                # 条件1：检测到段落间的停顿（有足够语音 + 静音足够长）
                if buffer_seconds >= min_speech_sec and silence_sec >= SILENCE_DURATION:
                    should_send = True
                # 条件2：累积超过25秒，强制分段发送
                elif buffer_seconds >= 25:
                    should_send = True
                # 条件3：至少3秒且有短暂停顿(0.8s)，实时反馈
                elif buffer_seconds >= 3 and silence_sec >= 0.8:
                    should_send = True

                if should_send:
                    max_window_sec = 25
                    max_window_bytes = int(max_window_sec * bytes_per_second)
                    if len(speech_buffer) > max_window_bytes:
                        audio_bytes = speech_buffer[-max_window_bytes:]
                        # 保留最后1秒作为上下文衔接
                        overlap = int(1.0 * bytes_per_second)
                        speech_buffer = speech_buffer[-overlap:]
                    else:
                        audio_bytes = speech_buffer
                        speech_buffer = b""
                    silence_frames = 0
                    segment_index += 1
                    await self._send_recognition(ws, audio_bytes, prefer_online)
                else:
                    await asyncio.sleep(0.1)

            # 停止前处理剩余音频
            if len(speech_buffer) >= 4000:
                await self._send_recognition(ws, speech_buffer, prefer_online)

        except Exception as e:
            await ws.send(json.dumps({
                "event": "error",
                "data": {"message": str(e)}
            }))
        finally:
            self._stop_recognition()

    async def _send_recognition(self, ws, audio_bytes, prefer_online, _last_text: str = ""):
        result = await self._recognize(audio_bytes, prefer_online)
        if result and result.get("text"):
            cmd = parse_command(result["text"])
            if cmd:
                await ws.send(json.dumps({"event": "command", "data": cmd}))
            else:
                await ws.send(json.dumps({
                    "event": "text",
                    "data": {
                        "text": result["text"],
                        "confidence": result["confidence"],
                        "is_final": result["is_final"],
                    }
                }))
        if result and result.get("error"):
            await ws.send(json.dumps({
                "event": "error",
                "data": {"message": result["error"]}
            }))

    async def _recognize(self, audio_bytes: bytes, prefer_online: bool) -> dict | None:
        """选择在线或离线识别，统一使用完整预处理管道"""
        orig_rate = self.capture.sample_rate

        # 完整预处理：重采样+降噪+高通滤波+归一化 → 干净 int16 PCM
        processed = _preprocess_audio(audio_bytes, orig_rate, TARGET_RATE)

        if prefer_online and self.baidu.api_key and self.baidu.check_available():
            return await asyncio.to_thread(self.baidu.recognize, processed, self.language, TARGET_RATE)
        elif whisper_available():
            audio_np = np.frombuffer(processed, dtype=np.int16).astype(np.float32) / 32768.0
            return await asyncio.to_thread(whisper_recognize, audio_np, self.language, self.script)
        return None

    def _stop_recognition(self):
        self.capture.stop()
        if self._task:
            self._task.cancel()
            self._task = None

    def _get_status(self) -> dict:
        return {
            "event": "status",
            "data": {
                "listening": self.capture._running,
                "online_available": self.baidu.check_available(),
                "offline_available": self._model_ready or whisper_available(),
                "model_loading": not self._model_ready,
                "language": self.language,
            }
        }

    async def _update_settings(self, msg: dict):
        api_key = msg.get("api_key", "")
        secret_key = msg.get("secret_key", "")
        if api_key:
            self.baidu.api_key = api_key
        if secret_key:
            self.baidu.secret_key = secret_key
        if "language" in msg:
            self.language = msg["language"]
        if "script" in msg:
            self.script = msg["script"]


def _detect_mic():
    """自动检测麦克风设备，返回 (device_index, sample_rate)
    优先选择物理麦克风，排除虚拟/环回设备，不依赖环境音量"""
    import subprocess, sys
    script = '''
import pyaudio

VIRTUAL = ["sound mapper", "主声音捕获", "立体声混音", "stereo mix", "主音量", "primary sound", "wave out"]
MIC_KW = ["麦克风", "microphone", "mic", "阵列"]

p = pyaudio.PyAudio()
real_fallback = None
any_fallback = None

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    name = info["name"]
    if info["maxInputChannels"] == 0:
        continue
    if any(k in name.lower() for k in VIRTUAL):
        continue

    is_mic = any(k in name.lower() for k in MIC_KW)
    default_rate = int(info["defaultSampleRate"])
    rates = [16000]
    if default_rate != 16000:
        rates.append(default_rate)

    for rate in rates:
        try:
            s = p.open(format=pyaudio.paInt16, channels=1, rate=rate,
                      input=True, input_device_index=i, frames_per_buffer=1024)
            s.read(1024, exception_on_overflow=False)
            s.stop_stream()
            s.close()
            if rate == 16000:
                print(f"OK:{i}:16000:{name}")
                p.terminate()
                raise SystemExit(0)
            if is_mic and real_fallback is None:
                real_fallback = (i, rate)
            elif any_fallback is None:
                any_fallback = (i, rate)
        except Exception:
            continue

p.terminate()
fb = real_fallback or any_fallback
if fb:
    print(f"OK:{fb[0]}:{fb[1]}:fallback")
else:
    print("NONE")
'''
    try:
        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True, text=True, timeout=15,
            cwd=sys.path[0] if sys.path[0] else None,
        )
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line.startswith('OK:'):
                parts = line.split(':', 3)
                idx, rate = int(parts[1]), int(parts[2])
                name = parts[3] if len(parts) > 3 else ''
                if rate == 16000:
                    return (idx, 16000)
                else:
                    print(f"麦克风(备选): [{idx}] {name} @ {rate}Hz (将重采样到16000)")
                    return (idx, rate)
            elif line == 'NONE':
                return None
    except Exception as e:
        print(f"设备检测异常: {e}")
    return None

def main():
    import os, sys
    host = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("YUSHENG_HOST", "127.0.0.1")
    port = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.environ.get("YUSHENG_PORT", "8765"))
    api_key = os.environ.get("YUSHENG_API_KEY", "")
    secret_key = os.environ.get("YUSHENG_SECRET_KEY", "")

    device_index = None
    sample_rate = 16000
    device_str = os.environ.get("YUSHENG_DEVICE")
    if device_str:
        device_index = int(device_str)
        print(f"使用指定麦克风: [{device_index}]")
    else:
        result = _detect_mic()
        if result:
            device_index, sample_rate = result
            print(f"自动检测麦克风: [{device_index}] @ {sample_rate}Hz")
        else:
            print("警告: 未检测到可用麦克风")

    server = VoiceServer(api_key=api_key, secret_key=secret_key,
                         device_index=device_index,
                         sample_rate=sample_rate)
    asyncio.run(server.start(host, port))


if __name__ == "__main__":
    main()
