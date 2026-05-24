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


class VoiceServer:
    def __init__(self, api_key: str = "", secret_key: str = "", device_index: int = None, sample_rate: int = 16000):
        self.capture = AudioCapture(device_index=device_index, sample_rate=sample_rate)
        self.baidu = BaiduASR(api_key=api_key, secret_key=secret_key)
        self.online_available = True
        self.language = "zh-CN"
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

        self.language = lang
        self.capture.start()

        self._task = asyncio.create_task(self._recognition_loop(ws, prefer_online))

    async def _recognition_loop(self, ws, prefer_online: bool):
        try:
            accumulated = b""
            while self.capture._running:
                # 快速读取所有可用音频
                chunk = self.capture.read_all()
                if chunk:
                    accumulated += chunk

                level = self.capture.get_audio_level()
                await ws.send(json.dumps({
                    "event": "audio_level",
                    "data": {"level": level}
                }))

                # 累积1秒音频后识别
                min_bytes = int(16000 * 1.0 * 2)
                if len(accumulated) < min_bytes:
                    await asyncio.sleep(0.1)
                    continue

                audio_bytes = accumulated
                accumulated = b""
                await self._send_recognition(ws, audio_bytes, prefer_online)

            # 停止前处理剩余音频
            if len(accumulated) >= 8000:
                await self._send_recognition(ws, accumulated, prefer_online)

        except Exception as e:
            await ws.send(json.dumps({
                "event": "error",
                "data": {"message": str(e)}
            }))
        finally:
            self._stop_recognition()

    async def _send_recognition(self, ws, audio_bytes, prefer_online):
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
        """选择在线或离线识别"""
        if prefer_online and self.baidu.api_key and self.baidu.check_available():
            return await asyncio.to_thread(self.baidu.recognize, audio_bytes, self.language)
        elif whisper_available():
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            return await asyncio.to_thread(whisper_recognize, audio_np, self.language)
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


def _detect_mic():
    """自动检测最可靠的麦克风设备，返回 (device_index, sample_rate)
    使用平均音量而非峰值来避免脉冲噪音被误判"""
    try:
        import pyaudio, numpy as np
        p = pyaudio.PyAudio()
        best = None  # (device, rate, avg_volume)
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] == 0:
                continue
            for rate in (16000, 44100):
                try:
                    stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate,
                                  input=True, input_device_index=i,
                                  frames_per_buffer=rate // 10)
                    vols = []
                    for _ in range(20):
                        data = stream.read(rate // 10, exception_on_overflow=False)
                        vol = int(np.max(np.abs(np.frombuffer(data, dtype=np.int16))) / 32768.0 * 100)
                        vols.append(vol)
                    stream.stop_stream()
                    stream.close()
                    avg_vol = sum(vols) / len(vols)
                    # 需要平均音量 > 10% 才认为是有效语音设备
                    if avg_vol > 10:
                        p.terminate()
                        return (i, rate)
                    # 记录备选
                    if avg_vol > 3 and (best is None or avg_vol > best[2]):
                        best = (i, rate, avg_vol)
                except Exception:
                    continue
        p.terminate()
        if best:
            return (best[0], best[1])
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
