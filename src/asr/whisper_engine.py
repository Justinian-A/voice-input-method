"""基于 Whisper 的语音识别引擎"""

from typing import Tuple, Optional
import numpy as np

from src.asr.base import ASREngine


class WhisperASR(ASREngine):
    """基于 OpenAI Whisper 的语音识别引擎

    优势：准确度高，多语言支持好
    劣势：响应速度较慢，资源消耗大
    适用场景：高精度转写，离线处理
    """

    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.model_size = config.get("model_size", "base")
        self.language = config.get("language", "zh")
        self.sample_rate = config.get("sample_rate", 16000)

    def load_model(self, model_path: str = None):
        """加载 Whisper 模型"""
        try:
            import whisper
            self.model = whisper.load_model(self.model_size)
        except ImportError:
            raise ImportError("请安装 whisper: pip install openai-whisper")

    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """识别音频数据"""
        if self.model is None:
            self.load_model()

        # 转换音频格式
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        # 执行识别
        result = self.model.transcribe(
            audio_array,
            language=self.language,
            fp16=False
        )

        text = result["text"].strip()
        # Whisper 不直接返回置信度，使用检测到的语言概率作为替代
        confidence = result.get("language_probability", 0.9)

        return text, confidence

    def recognize_stream(self, audio_chunk: bytes) -> Tuple[str, bool]:
        """流式识别（Whisper 不原生支持流式，需累积音频）"""
        # 简单实现：累积音频后一次性识别
        text, confidence = self.recognize(audio_chunk)
        return text, True

    def unload_model(self):
        """卸载模型"""
        self.model = None
