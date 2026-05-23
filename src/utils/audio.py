"""音频采集与处理工具"""

import threading
from typing import Callable, Optional
from collections import deque

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None


class AudioCapture:
    """音频采集器

    功能：
    - 实时音频采集
    - VAD（语音活动检测）
    - 音频缓冲
    """

    def __init__(self, config: dict):
        self.config = config
        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.dtype = config.get("dtype", "int16")
        self.vad_threshold = config.get("vad_threshold", 0.5)

        self._is_recording = False
        self._callback: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None
        self._buffer: deque = deque(maxlen=100)
        self._stream = None

    def start(self, callback: Callable[[bytes], None]):
        """开始录音

        Args:
            callback: 音频数据回调函数
        """
        if self._is_recording:
            return

        if sd is None:
            raise ImportError("请安装 sounddevice: pip install sounddevice")

        self._callback = callback
        self._is_recording = True

        # 启动录音线程
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止录音"""
        self._is_recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _record_loop(self):
        """录音主循环"""
        try:
            # 计算块大小（samples per block）
            blocksize = int(self.sample_rate * 0.1)  # 100ms blocks

            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"音频状态: {status}")

                # VAD检测
                if self._is_speech(indata):
                    audio_bytes = indata.tobytes()
                    self._buffer.append(audio_bytes)

                    # 当缓冲区足够大时，触发回调
                    if len(self._buffer) >= 5:  # 500ms
                        combined = b"".join(self._buffer)
                        self._buffer.clear()
                        if self._callback:
                            self._callback(combined)

            # 打开音频流
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=blocksize,
                callback=audio_callback
            )

            self._stream.start()

            # 保持线程运行
            while self._is_recording:
                sd.sleep(100)

        except Exception as e:
            print(f"录音错误: {e}")
            self._is_recording = False

    def _is_speech(self, audio_data: np.ndarray) -> bool:
        """简单的 VAD 检测

        使用能量阈值判断是否有人声
        """
        # 计算音频能量
        energy = np.abs(audio_data).mean()

        # 与阈值比较
        return energy > self.vad_threshold * 1000

    def get_buffer(self) -> bytes:
        """获取缓冲区中的所有音频数据"""
        if not self._buffer:
            return b""
        combined = b"".join(self._buffer)
        self._buffer.clear()
        return combined

    @property
    def is_recording(self) -> bool:
        """是否正在录音"""
        return self._is_recording
