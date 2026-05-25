"""
Whisper 离线语音识别模块（faster-whisper 后端，CPU 优化）
"""

import os
import numpy as np
from faster_whisper import WhisperModel


MODEL = None
MODEL_SIZE = "medium"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "whisper")


def _model_cached(size: str = "medium") -> bool:
    """检查模型文件是否已缓存"""
    model_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
    import glob
    pattern = os.path.join(model_dir, f"*faster-whisper-{size}*")
    return len(glob.glob(pattern)) > 0 or os.path.exists(os.path.join(CACHE_DIR, f"{size}.pt"))


def load_model(size: str = "medium"):
    """加载 Whisper 模型（faster-whisper int8 量化，CPU 上快 4 倍）"""
    global MODEL, MODEL_SIZE
    if MODEL is None or MODEL_SIZE != size:
        MODEL_SIZE = size
        MODEL = WhisperModel(size, device="cpu", compute_type="int8")
    return MODEL


def recognize(audio_data: np.ndarray, language: str = "zh", script: str = "simplified") -> dict:
    """使用 faster-whisper 本地模型识别"""
    model = load_model()

    lang_map = {"zh": "zh", "zh-CN": "zh", "en": "en", "en-US": "en"}
    lang = lang_map.get(language, "zh")

    segments, info = model.transcribe(
        audio_data,
        language=lang,
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False,
        no_speech_threshold=0.4,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=400,
            speech_pad_ms=200,
        ),
    )

    texts = []
    segments_list = list(segments)
    for seg in segments_list:
        t = seg.text.strip()
        if t:
            texts.append(t)

    text = "".join(texts)

    # 简体中文后处理
    if lang == "zh" and script == "simplified" and text:
        try:
            import zhconv
            text = zhconv.convert(text, 'zh-cn')
        except ImportError:
            pass

    # 计算信心度
    confidence = 1.0
    if segments_list:
        probs = [s.no_speech_prob for s in segments_list]
        confidence = 1.0 - np.mean(probs)

    return {
        "text": text,
        "confidence": float(confidence),
        "is_final": True,
        "error": None,
    }


def check_available() -> bool:
    """检查 Whisper 模型是否已缓存"""
    return _model_cached(MODEL_SIZE)
