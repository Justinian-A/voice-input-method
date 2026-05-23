"""语音识别引擎基类"""

from abc import ABC, abstractmethod
from typing import Tuple


class ASREngine(ABC):
    """语音识别引擎抽象基类"""

    @abstractmethod
    def load_model(self, model_path: str = None):
        """加载模型"""
        pass

    @abstractmethod
    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """
        识别音频数据

        Args:
            audio_data: 音频数据(bytes)

        Returns:
            Tuple[str, float]: (识别文本, 置信度)
        """
        pass

    @abstractmethod
    def recognize_stream(self, audio_chunk: bytes) -> Tuple[str, bool]:
        """
        流式识别音频块

        Args:
            audio_chunk: 音频数据块

        Returns:
            Tuple[str, bool]: (识别文本, 是否为最终结果)
        """
        pass

    @abstractmethod
    def unload_model(self):
        """卸载模型，释放资源"""
        pass
