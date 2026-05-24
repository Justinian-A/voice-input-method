"""
音频采集模块
使用 PyAudio 进行实时音频采集
"""

import threading
import queue
import numpy as np

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False


class AudioCapture:
    """实时音频采集器"""

    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self._audio = None
        self._stream = None
        self._running = False
        self._thread = None
        self._queue = queue.Queue(maxsize=100)
        self._buffer = []

    def start(self):
        """开始采集音频"""
        if not HAS_PYAUDIO:
            raise RuntimeError("PyAudio 未安装，无法采集音频")

        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """采集线程"""
        while self._running:
            try:
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                self._queue.put(data)
                self._buffer.append(data)
            except Exception:
                break

    def read(self, timeout=0.1) -> bytes:
        """读取音频数据块"""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return b""

    def read_accumulated(self, duration_sec: float) -> bytes:
        """读取累积指定时长的音频数据"""
        frames_needed = int(self.sample_rate * duration_sec / self.chunk_size)
        while len(self._buffer) < frames_needed:
            try:
                data = self._queue.get(timeout=0.05)
                self._buffer.append(data)
            except queue.Empty:
                break
        result = b"".join(self._buffer)
        self._buffer = []
        return result

    def get_audio_level(self) -> float:
        """获取当前音量级别 (0.0-1.0)"""
        if not self._buffer:
            return 0.0
        recent = self._buffer[-10:] if len(self._buffer) > 10 else self._buffer
        audio_data = b"".join(recent)
        if not audio_data:
            return 0.0
        samples = np.frombuffer(audio_data, dtype=np.int16)
        level = np.abs(samples).mean() / 32768.0
        return min(float(level * 5), 1.0)  # 放大5倍便于显示

    def stop(self):
        """停止采集"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._audio:
            self._audio.terminate()
