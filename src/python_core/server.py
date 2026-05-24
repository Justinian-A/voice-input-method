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
    def __init__(self):
        self.capture = AudioCapture()
        self.baidu = BaiduASR()
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
            while self.capture._running:
                # 每隔1秒发送一次音频到识别引擎
                audio_bytes = self.capture.read_accumulated(1.0)
                if not audio_bytes:
                    await asyncio.sleep(0.1)
                    continue

                # 发送音量级别
                level = self.capture.get_audio_level()
                await ws.send(json.dumps({
                    "event": "audio_level",
                    "data": {"level": level}
                }))

                result = await self._recognize(audio_bytes, prefer_online)

                if result and result.get("text"):
                    # 检查是否为语音命令
                    cmd = parse_command(result["text"])
                    if cmd:
                        await ws.send(json.dumps({
                            "event": "command",
                            "data": cmd
                        }))
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

        except Exception as e:
            await ws.send(json.dumps({
                "event": "error",
                "data": {"message": str(e)}
            }))
        finally:
            self._stop_recognition()

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


def main():
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    server = VoiceServer()
    asyncio.run(server.start(host, port))


if __name__ == "__main__":
    main()
