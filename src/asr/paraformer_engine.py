"""基于 Paraformer 的语音识别引擎"""

from typing import Tuple
import numpy as np

from src.asr.base import ASREngine


class ParaformerASR(ASREngine):
    """基于 FunASR Paraformer 的语音识别引擎

    优势：响应速度快，支持流式识别，中文识别效果好
    劣势：多语言支持相对弱
    适用场景：实时语音输入，中文场景
    """

    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.sample_rate = config.get("sample_rate", 16000)
        self.language = config.get("language", "zh")

    def load_model(self, model_path: str = None):
        """加载 Paraformer 模型"""
        try:
            from funasr import AutoModel

            model_id = model_path or "paraformer-zh"
            self.model = AutoModel(
                model=model_id,
                vad_model="fsmn-vad",
                punc_model="ct-punc",
                device="cpu"
            )
        except ImportError:
            raise ImportError("请安装 FunASR: pip install funasr")

    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """识别音频数据"""
        if self.model is None:
            self.load_model()

        # 转换音频格式
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        # 执行识别
        result = self.model.generate(
            input=audio_array,
            batch_size_s=300
        )

        if result and len(result) > 0:
            text = result[0].get("text", "")
            confidence = result[0].get("confidence", 0.9)
            return text, confidence

        return "", 0.0

    def recognize_stream(self, audio_chunk: bytes) -> Tuple[str, bool]:
        """流式识别"""
        if self.model is None:
            self.load_model()

        audio_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

        result = self.model.generate(
            input=audio_array,
            batch_size_s=300,
            is_final=False
        )

        if result and len(result) > 0:
            text = result[0].get("text", "")
            is_final = result[0].get("is_final", True)
            return text, is_final

        return "", True

    def unload_model(self):
        """卸载模型"""
        self.model = None
