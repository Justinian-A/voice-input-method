"""
Whisper 离线语音识别模块
"""

import os
import numpy as np
import whisper


MODEL = None
MODEL_SIZE = "base"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "whisper")


def _model_cached(size: str = "base") -> bool:
    """检查模型文件是否已缓存"""
    return os.path.exists(os.path.join(CACHE_DIR, f"{size}.pt"))


def load_model(size: str = "base"):
    """加载 Whisper 模型（复用实例，下载在子线程中执行）"""
    global MODEL, MODEL_SIZE
    if MODEL is None or MODEL_SIZE != size:
        MODEL_SIZE = size
        MODEL = whisper.load_model(size)
    return MODEL


def recognize(audio_data: np.ndarray, language: str = "zh") -> dict:
    """使用 Whisper 本地模型识别"""
    model = load_model()

    lang_map = {"zh": "zh", "zh-CN": "zh", "en": "en", "en-US": "en"}
    lang = lang_map.get(language, "zh")

    result = model.transcribe(
        audio_data,
        language=lang,
        fp16=False,
        no_speech_threshold=0.6,
    )

    text = result.get("text", "").strip()
    segments = result.get("segments", [])
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
    """检查 Whisper 模型是否已缓存（不加载，避免阻塞）"""
    return _model_cached(MODEL_SIZE)
