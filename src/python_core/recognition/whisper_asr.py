"""
Whisper 离线语音识别模块
"""

import numpy as np
import whisper


MODEL = None
MODEL_SIZE = "base"


def load_model(size: str = "base"):
    """加载 Whisper 模型（复用实例）"""
    global MODEL, MODEL_SIZE
    if MODEL is None or MODEL_SIZE != size:
        MODEL_SIZE = size
        MODEL = whisper.load_model(size)
    return MODEL


def recognize(audio_data: np.ndarray, language: str = "zh") -> dict:
    """
    使用 Whisper 本地模型识别
    audio_data: float32 numpy array, 16kHz sample rate
    """
    model = load_model()

    # Whisper 语言映射
    lang_map = {"zh": "zh", "zh-CN": "zh", "en": "en", "en-US": "en"}
    lang = lang_map.get(language, "zh")

    result = model.transcribe(
        audio_data,
        language=lang,
        fp16=False,  # Windows CPU 模式
        no_speech_threshold=0.6,
    )

    text = result.get("text", "").strip()
    segments = result.get("segments", [])

    # 计算平均置信度
    confidence = 1.0
    if segments:
        confidences = [s.get("no_speech_prob", 0.0) for s in segments]
        confidence = 1.0 - np.mean(confidences)

    return {
        "text": text,
        "confidence": float(confidence),
        "is_final": True,
        "error": None,
    }


def check_available() -> bool:
    """检测 Whisper 模型是否可用"""
    try:
        load_model()
        return True
    except Exception:
        return False
