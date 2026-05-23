"""语音输入法核心引擎"""

from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

from src.asr.base import ASREngine
from src.asr.whisper_engine import WhisperASR
from src.asr.paraformer_engine import ParaformerASR
from src.nlp.processor import NLPProcessor
from src.utils.audio import AudioCapture


class EngineState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class RecognitionResult:
    text: str
    confidence: float
    is_final: bool
    language: str
    duration: float


class VoiceInputEngine:
    """语音输入法核心引擎，协调各模块工作"""

    def __init__(self, config: dict):
        self.config = config
        self.state = EngineState.IDLE
        self._callbacks: list[Callable] = []

        # 初始化各模块
        self.asr = self._init_asr()
        self.nlp = NLPProcessor(config.get("nlp", {}))
        self.audio = AudioCapture(config.get("audio", {}))

        # 热词
        self.hotwords: list[str] = []
        self._load_hotwords()

    def _init_asr(self) -> ASREngine:
        """初始化语音识别引擎"""
        asr_config = self.config.get("asr", {})
        engine_type = asr_config.get("engine", "paraformer")

        if engine_type == "whisper":
            return WhisperASR(asr_config)
        return ParaformerASR(asr_config)

    def _load_hotwords(self):
        """加载热词"""
        hotwords_config = self.config.get("hotwords", {})
        if not hotwords_config.get("enabled"):
            return

        hotwords_file = hotwords_config.get("file")
        if hotwords_file:
            try:
                with open(hotwords_file, "r", encoding="utf-8") as f:
                    self.hotwords = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                pass

    def on_result(self, callback: Callable[[RecognitionResult], None]):
        """注册识别结果回调"""
        self._callbacks.append(callback)

    def _notify(self, result: RecognitionResult):
        """通知所有回调"""
        for callback in self._callbacks:
            callback(result)

    def start_listening(self):
        """开始语音识别"""
        self.state = EngineState.LISTENING
        self.audio.start(callback=self._on_audio_data)

    def stop_listening(self):
        """停止语音识别"""
        self.audio.stop()
        self.state = EngineState.IDLE

    def _on_audio_data(self, audio_data: bytes):
        """处理音频数据"""
        self.state = EngineState.PROCESSING

        # 语音识别
        raw_text, confidence = self.asr.recognize(audio_data)

        # NLP后处理
        processed_text = self.nlp.process(raw_text)

        # 热词替换
        if self.hotwords:
            processed_text = self._apply_hotwords(processed_text)

        result = RecognitionResult(
            text=processed_text,
            confidence=confidence,
            is_final=True,
            language=self.config.get("asr", {}).get("language", "zh"),
            duration=0.0
        )

        self._notify(result)
        self.state = EngineState.LISTENING

    def _apply_hotwords(self, text: str) -> str:
        """应用热词替换"""
        for hotword in self.hotwords:
            if hotword in text:
                continue  # 已存在，无需替换
        return text

    def get_state(self) -> EngineState:
        """获取引擎状态"""
        return self.state
