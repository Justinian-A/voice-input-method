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

    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1, device_index=None):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        self._audio = None
        self._stream = None
        self._running = False
        self._thread = None
        self._queue = queue.Queue(maxsize=200)
        self._buffer = []

    def start(self):
        """开始采集音频"""
        if not HAS_PYAUDIO:
            raise RuntimeError("PyAudio 未安装，无法采集音频")

        # 清理上一轮的残留数据
        self._queue = queue.Queue(maxsize=200)
        self._buffer = []

        self._audio = pyaudio.PyAudio()
        stream_kwargs = {
            "format": pyaudio.paInt16,
            "channels": self.channels,
            "rate": self.sample_rate,
            "input": True,
            "frames_per_buffer": self.chunk_size,
        }
        if self.device_index is not None:
            stream_kwargs["input_device_index"] = self.device_index
        self._stream = self._audio.open(**stream_kwargs)
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
                # 限制buffer大小，保留最近2秒
                max_buffer = int(self.sample_rate * 2 / self.chunk_size)
                if len(self._buffer) > max_buffer:
                    self._buffer = self._buffer[-max_buffer:]
            except Exception:
                break

    def read(self, timeout=0.1) -> bytes:
        """读取单个音频数据块"""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return b""

    def read_all(self) -> bytes:
        """读取当前队列中的所有音频数据"""
        chunks = []
        while True:
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return b"".join(chunks)

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
        return min(float(level * 5), 1.0)

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

        # 清理残留
        self._stream = None
        self._audio = None
        self._thread = None
